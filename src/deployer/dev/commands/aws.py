"""
Creates a new typer application, which is then
nested as a sub-command named "aws"
under the `exec` sub-command of the deployer.

Helper methods for commandline access to AWS.

Google Cloud's `gcloud` is more user friendly than AWS's `aws`,
so we have some augmented methods here primarily for AWS use.
"""

import json
import os
import re
import secrets
import string
import subprocess
import tempfile
import textwrap

import typer

from deployer.dev.app import CLOUD, app
from deployer.utils.rendering import print_colour

aws = typer.Typer(pretty_exceptions_show_locals=False)
app.add_typer(
    aws,
    name="aws",
    rich_help_panel=CLOUD,
    help="AWS helpers.",
)


class STSEnvSetupError(RuntimeError): ...


def setup_aws_sts_env(profile, mfa_device_id, auth_token) -> dict[str, str]:
    env = os.environ | {
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": "",
        "AWS_SESSION_TOKEN": "",
        "AWS_PROFILE": profile,
    }
    if mfa_device_id and auth_token:
        result = subprocess.run(
            [
                "aws",
                "sts",
                "get-session-token",
                "--serial-number",
                mfa_device_id,
                "--token-code",
                str(auth_token),
                "--profile",
                profile,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise STSEnvSetupError(result.stderr)

        creds = json.loads(result.stdout)
        env["AWS_ACCESS_KEY_ID"] = creds["Credentials"]["AccessKeyId"]
        env["AWS_SECRET_ACCESS_KEY"] = creds["Credentials"]["SecretAccessKey"]
        env["AWS_SESSION_TOKEN"] = creds["Credentials"]["SessionToken"]
        return env

    # Help caller by checking the session is valid
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )
    # Valid login
    if not result.returncode:
        return env

    # Not an SSO log-in problem, throw an error
    if not re.search(
        r"Error loading SSO Token|SSO session associated with this profile has expired or is otherwise invalid",
        result.stderr,
    ):
        raise STSEnvSetupError(result.stderr)

    # SSO log-in problem, try and log-in
    result = subprocess.run(
        ["aws", "sso", "login", "--profile", profile],
        text=True,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise STSEnvSetupError(result.stderr)

    # Ensure log-in is valid (log-in does not test SSO role)
    result = subprocess.run(
        ["aws", "sts", "get-caller-identity", "--profile", profile],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise STSEnvSetupError(result.stderr)

    # Successful login
    return env


# Invalid login without SSO


@aws.command(context_settings={"allow_extra_args": True})
def shell(
    ctx: typer.Context,
    profile: str = typer.Argument(..., help="Name of AWS profile to operate on"),
    mfa_device_id: str = typer.Argument(
        None,
        help="Full ARN of MFA Device the code is from (leave empty if not using MFA, e.g if using SSO)",
    ),
    auth_token: str = typer.Argument(
        None,
        help="6 digit 2 factor authentication code from the MFA device (leave empty if not using MFA)",
    ),
):
    """
    Exec into a shell with appropriate AWS credentials (including MFA)
    """
    try:
        env = setup_aws_sts_env(profile, mfa_device_id, auth_token)
    except STSEnvSetupError as err:
        raise SystemExit(*err.args)

    args = [os.environ["SHELL"], "-l"]
    if ctx.args:
        args.extend(("-c", " ".join(ctx.args)))

    subprocess.check_call(args, env=env)


@aws.command()
def offboard(
    username: str = typer.Argument(..., help="Username to offboard from AWS"),
    profile: str = typer.Argument(..., help="Name of AWS profile to operate on"),
    mfa_device_id: str = typer.Argument(
        None,
        help="Full ARN of MFA Device the code is from (leave empty if not using MFA)",
    ),
    auth_token: str = typer.Argument(
        None,
        help="6 digit 2 factor authentication code from the MFA device (leave empty if not using MFA)",
    ),
):
    env = setup_aws_sts_env(profile, mfa_device_id, auth_token)
    print(f"Offboarding {username} from AWS account {profile}")
    access_keys = json.loads(
        subprocess.check_output(
            ["aws", "iam", "list-access-keys", "--user-name", username],
            env=env,
        ).decode()
    )

    # Delete all access keys for the user
    if access_keys["AccessKeyMetadata"]:
        for key in access_keys["AccessKeyMetadata"]:
            access_key_id = key["AccessKeyId"]
            print_colour(f"Deleting {access_key_id} for user {username}", "yellow")
            subprocess.check_call(
                [
                    "aws",
                    "iam",
                    "delete-access-key",
                    "--user-name",
                    username,
                    "--access-key-id",
                    access_key_id,
                ],
                env=env,
            )
            print_colour("Done")
    else:
        print_colour(f"No existing access keys found for user {username}")

    # Delete the user from all groups
    groups = json.loads(
        subprocess.check_output(
            ["aws", "iam", "list-groups-for-user", "--user-name", username],
            env=env,
        ).decode()
    )
    if groups["Groups"]:
        print(f"Removing {username} from all {groups} groups...")
        for group in groups["Groups"]:
            group_name = group["GroupName"]
            print_colour(f"Removing {username} from group {group_name}", "yellow")
            subprocess.check_call(
                [
                    "aws",
                    "iam",
                    "remove-user-from-group",
                    "--user-name",
                    username,
                    "--group-name",
                    group_name,
                ],
                env=env,
            )
            print_colour("Done!")
    else:
        print_colour(f"No existing groups found for user {username}")

    # Delete the user's virtual MFA devices
    mfa_devices = json.loads(
        subprocess.check_output(
            ["aws", "iam", "list-virtual-mfa-devices"],
            env=env,
        ).decode()
    )[["VirtualMFADevices"]]
    for device in mfa_devices:
        if device.get("User", {}).get("UserName", "") == username:
            print(f"Removing virtual MFA devices for user {username}...")
            mfa = device["SerialNumber"]
            print_colour(
                f"Deactivating and deleting virtual MFA device {mfa} for user {username}",
                "yellow",
            )
            subprocess.check_call(
                [
                    "aws",
                    "iam",
                    "deactivate-mfa-device",
                    "--user-name",
                    username,
                    "--serial-number",
                    mfa,
                ],
                env=env,
            )
            subprocess.check_call(
                ["aws", "iam", "delete-virtual-mfa-device", "--serial-number", mfa],
                env=env,
            )
            print_colour("Done!")
        else:
            print_colour(f"No virtual MFA devices found for user {username}")

    # Delete the user's login profile
    print(f"Deleting login profile for user {username}...")
    subprocess.check_call(
        ["aws", "iam", "delete-login-profile", "--user-name", username],
        env=env,
    )
    print_colour("Done!")

    subprocess.check_call(
        ["aws", "iam", "delete-user", "--user-name", username],
        env=env,
    )
    print_colour(f"User {username} has been deleted from AWS account {profile}.")


@aws.command()
def onboard(
    new_username: str = typer.Argument(..., help="Username to onboard to AWS account"),
    existing_username: str = typer.Argument(
        ...,
        help="Username of an existing user to copy group memberships and policies from",
    ),
    profile: str = typer.Argument(..., help="Name of AWS profile to operate on"),
    mfa_device_id: str = typer.Argument(
        None,
        help="Full ARN of MFA Device the code is from (leave empty if not using MFA)",
    ),
    auth_token: str = typer.Argument(
        None,
        help="6 digit 2 factor authentication code from the MFA device (leave empty if not using MFA)",
    ),
):
    env = setup_aws_sts_env(profile, mfa_device_id, auth_token)
    print(f"Onboarding {new_username} to AWS account {profile}")

    # Check if the existing user actually exists
    subprocess.check_call(
        ["aws", "iam", "get-user", "--user-name", existing_username], env=env
    )

    # Check if the new user exists
    password = None
    try:
        subprocess.check_call(
            ["aws", "iam", "get-user", "--user-name", new_username], env=env
        )
    except subprocess.CalledProcessError as error:
        print(f"Creating user {new_username}...")
        subprocess.check_call(
            ["aws", "iam", "create-user", "--user-name", new_username], env=env
        )

        # Generate and assign password
        alphabet = string.ascii_letters + string.digits + string.punctuation
        password = "".join(secrets.choice(alphabet) for _ in range(20))

        print(f"The generated password for {new_username} is: {password}")
        subprocess.check_call(
            [
                "aws",
                "iam",
                "create-login-profile",
                "--user-name",
                new_username,
                "--password",
                password,
                "--password-reset-required",
            ],
            env=env,
        )
        print_colour("Done! Login profile created")

    # Copy group memberships from another existing user
    print("Copying group memberships...")
    groups = json.loads(
        subprocess.check_output(
            ["aws", "iam", "list-groups-for-user", "--user-name", existing_username],
            env=env,
        ).decode()
    )

    for group in groups["Groups"]:
        print(f"Adding to group: {group['GroupName']}")
        subprocess.check_call(
            [
                "aws",
                "iam",
                "add-user-to-group",
                "--user-name",
                new_username,
                "--group-name",
                group["GroupName"],
            ],
            env=env,
        )
        print_colour("Done!")

    # Copy managed policies from another existing user
    print("Copying attached managed policies...")
    policies = json.loads(
        subprocess.check_output(
            [
                "aws",
                "iam",
                "list-attached-user-policies",
                "--user-name",
                existing_username,
                "--query",
                "AttachedPolicies[].PolicyArn",
                "--output",
                "json",
            ],
            env=env,
        ).decode()
    )
    for policy_arn in policies:
        print(f"Attaching policy: {policy_arn}")
        subprocess.check_call(
            [
                "aws",
                "iam",
                "attach-user-policy",
                "--user-name",
                new_username,
                "--policy-arn",
                policy_arn,
            ],
            env=env,
        )
    print_colour("Done!")
    # Copy inline policies
    print("Copying inline policies...")
    inline_list = json.loads(
        subprocess.check_output(
            [
                "aws",
                "iam",
                "list-user-policies",
                "--user-name",
                existing_username,
                "--query",
                "PolicyNames",
                "--output",
                "json",
            ],
            env=env,
        ).decode()
    )
    for policy_name in inline_list:
        print(f"Copying inline policy: {policy_name}")
        policy_doc = json.loads(
            subprocess.check_output(
                [
                    "aws",
                    "iam",
                    "get-user-policy",
                    "--user-name",
                    existing_username,
                    "--policy-name",
                    policy_name,
                    "--query",
                    "PolicyDocument",
                    "--output",
                    "json",
                ],
                env=env,
            ).decode()
        )
        with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
            json.dump(policy_doc, temp_file)
            temp_file.flush()
            subprocess.check_call(
                [
                    "aws",
                    "iam",
                    "put-user-policy",
                    "--user-name",
                    new_username,
                    "--policy-name",
                    policy_name,
                    "--policy-document",
                    f"file://{temp_file.name}",
                ],
                env=env,
            )

    print_colour("Done!")
    account_id = (
        subprocess.check_output(
            [
                "aws",
                "sts",
                "get-caller-identity",
                "--query",
                "Account",
                "--output",
                "text",
            ],
            env=env,
        )
        .decode()
        .strip()
    )
    if password:
        print_colour(
            textwrap.dedent(f"""
                Hey {new_username}! I have created an account for you in {profile}.
                The password was randomly generated and you must change it on first login.

                Use the following link to log in: https://{account_id}.signin.aws.amazon.com/console
                The password is: {password}
                """),
            "yellow",
        )
    else:
        print_colour(
            f"{new_username} permissions have been updated in {profile}-{account_id} AWS account.",
            "yellow",
        )
