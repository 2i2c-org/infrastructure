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
import subprocess

import typer

from deployer.cli_app import exec_app
from deployer.utils.rendering import print_colour

aws = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(
    aws,
    name="aws",
    help="Helper methods for commandline access to AWS.",
)


def setup_aws_env(profile, mfa_device_id, auth_token) -> dict[str, str]:
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
        env=setup_aws_env(profile, mfa_device_id, auth_token),
    )


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
    env = setup_aws_env(profile, mfa_device_id, auth_token)
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
        ).decode()["Groups"]
    )
    if groups:
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
