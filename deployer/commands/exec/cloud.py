"""
Helper methods for commandline access to cloud providers.

Google Cloud's `gcloud` is more user friendly than AWS's `aws`,
so we have some augmented methods here primarily for AWS use.
"""

import json
import os
import subprocess

import typer

from deployer.cli_app import exec_app


@exec_app.command()
def aws(
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
        env["AWS_ACCESS_KEY_ID"] = (creds["Credentials"]["AccessKeyId"],)
        env["AWS_SECRET_ACCESS_KEY"] = (creds["Credentials"]["SecretAccessKey"],)
        env["AWS_SESSION_TOKEN"] = creds["Credentials"]["SessionToken"]

    subprocess.check_call([os.environ["SHELL"], "-l"], env=env)
