"""
Creates a new typer application, which is then
nested as a sub-command named "aws"
under the `exec` sub-command of the deployer.

Helper methods for commandline access to AWS.

Google Cloud's `gcloud` is more user friendly than AWS's `aws`,
so we have some augmented methods here primarily for AWS use.
"""

import configparser
import json
import os
import secrets
import string
import subprocess
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path

import typer
from rich.prompt import Prompt

from deployer.cli_app import exec_app
from deployer.utils.rendering import print_colour

aws = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(
    aws,
    name="aws",
    help="Helper methods for commandline access to AWS.",
)


def setup_aws_sts_env(profile, mfa_device_id, auth_token) -> dict[str, str]:
    env = os.environ | {
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": "",
        "AWS_SESSION_TOKEN": "",
        "AWS_PROFILE": profile,
    }
    if mfa_device_id and auth_token:
        creds = json.loads(
            subprocess.check_output(
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
                ]
            ).decode()
        )
        env["AWS_ACCESS_KEY_ID"] = creds["Credentials"]["AccessKeyId"]
        env["AWS_SECRET_ACCESS_KEY"] = creds["Credentials"]["SecretAccessKey"]
        env["AWS_SESSION_TOKEN"] = creds["Credentials"]["SessionToken"]
    return env


def list_sso_accounts(profile, access_token):
    accounts_list_json = subprocess.check_output(
        [
            "aws",
            "sso",
            "list-accounts",
            "--access-token",
            access_token,
            "--profile",
            profile,
            "--output",
            "json",
        ]
    )

    accounts_list = json.loads(accounts_list_json).get("accountList", "")
    if not accounts_list:
        print_colour("No accountList in aws response. Aborting...", "red")
    return {acc["accountName"]: acc["accountId"] for acc in accounts_list}


def list_account_roles(profile, account_id, access_token):
    roles = json.loads(
        subprocess.check_output(
            [
                "aws",
                "sso",
                "list-account-roles",
                "--access-token",
                access_token,
                "--account-id",
                account_id,
                "--profile",
                profile,
                "--output",
                "json",
            ]
        )
    ).get("roleList", "")
    return {role["roleName"] for role in roles}


def get_role_creds_as_env(profile, account_id, role, access_token):
    creds_json = subprocess.check_output(
        [
            "aws",
            "sso",
            "get-role-credentials",
            "--account-id",
            account_id,
            "--role-name",
            role,
            "--access-token",
            access_token,
            "--profile",
            profile,
            "--output",
            "json",
        ]
    )

    creds = json.loads(creds_json).get("roleCredentials", "")
    if not creds:
        print_colour("No role credentials in aws response. Aborting...", "red")
        return

    return os.environ | {
        "AWS_ACCESS_KEY_ID": creds["accessKeyId"],
        "AWS_SECRET_ACCESS_KEY": creds["secretAccessKey"],
        "AWS_SESSION_TOKEN": creds["sessionToken"],
    }


@aws.command()
def shell(
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
    """
    Exec into a shell with appropriate AWS credentials (including MFA)
    """

    subprocess.check_call(
        [os.environ["SHELL"], "-l"],
        env=setup_aws_sts_env(profile, mfa_device_id, auth_token),
    )


@aws.command()
def sso_shell(
    profile: str = typer.Argument(..., help="Name of AWS SSO profile to login into"),
    account_name: str = typer.Argument(
        "",
        help="The name of the account under SSO that you want to login into",
    ),
    role: str = typer.Argument("", help="What role to assume"),
    cmd: str = typer.Argument("", help="Command to execute inside the shell"),
):
    """
    Exec into a shell with appropriate AWS credentials for an account under SSO
    """

    cache_dir = Path.home() / ".aws" / "sso" / "cache"
    cache_files = list(cache_dir.glob("*.json"))

    # Get the start_url of the profile
    config_path = Path(os.environ.get("AWS_CONFIG_FILE", "~/.aws/config")).expanduser()
    parser = configparser.ConfigParser()
    parser.read(config_path)
    profile_config = parser[f"profile {profile}"]
    try:
        sso_start_url = profile_config["sso_start_url"]
    except KeyError:
        sso_session_name = profile_config["sso_session"]
        sso_session_config = parser[f"sso-session {sso_session_name}"]
        sso_start_url = sso_session_config["sso_start_url"]

    def needs_sso_login():
        if not cache_files:
            return True
        latest_cache_file = max(cache_files, key=os.path.getctime)
        try:
            with open(latest_cache_file) as f:
                data = json.load(f)
            expires_at_str = data.get("expiresAt")
            url = data.get("startUrl")
            if url != sso_start_url:
                return True
            if not expires_at_str:
                return True

            # Verify if the cached token has expired
            expires_at = datetime.fromisoformat(expires_at_str)
            return datetime.now(expires_at.tzinfo) >= expires_at
        except:
            return True

    # Get the access token from th cached file
    if needs_sso_login():
        print_colour(
            "SSO token expired or missing. Running 'aws sso login'...", "yellow"
        )
        subprocess.check_call(["aws", "sso", "login", "--profile", profile])
        print_colour("Login complete")

    if not cache_files:
        print_colour("No SSO cache after login. Check SSO config.", "red")
        return

    latest_cache_file = max(cache_files, key=os.path.getctime)
    with open(latest_cache_file) as f:
        data = json.load(f)

    access_token = data.get("accessToken", "")
    if not access_token:
        print_colour("Token is missing from the cache file. Aborting...", "red")

    # Resolve account name to ID
    accounts = list_sso_accounts(profile, access_token)
    if not account_name:
        account_name = Prompt.ask(
            ":point_right: What account name do you want to access?",
            choices=accounts.keys(),
        )

    if account_name not in accounts:
        print_colour(
            f"Account '{account_name}' not found. Available: {list(accounts.keys())}",
            "yellow",
        )
        return

    account_id = accounts[account_name]
    print_colour(f"Resolved '{account_name}' to account ID {account_id}")

    roles = list_account_roles(profile, account_id, access_token)
    if not role:
        role = Prompt.ask(
            f":point_right: What role do you want to assume in {account_name}",
            choices=roles,
        )

    # Get role credentials
    print_colour(
        f"Fetching credentials for account {account_id}, role {role}...", "yellow"
    )
    env = get_role_creds_as_env(profile, account_id, role, access_token)

    print_colour(
        f"✅ New shell ready for account {account_name}:{account_id}, role {role}"
    )
    print_colour(
        "💡 Run 'eksctl get cluster --region=<cluster_region>' to verify", "yellow"
    )

    subprocess.check_call([os.environ["SHELL"], "-l", "-c", cmd], env=env)


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
            textwrap.dedent(
                f"""
                Hey {new_username}! I have created an account for you in {profile}.
                The password was randomly generated and you must change it on first login.

                Use the following link to log in: https://{account_id}.signin.aws.amazon.com/console
                The password is: {password}
                """
            ),
            "yellow",
        )
    else:
        print_colour(
            f"{new_username} permissions have been updated in {profile}-{account_id} AWS account.",
            "yellow",
        )
