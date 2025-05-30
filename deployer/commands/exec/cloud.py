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
        ..., help="Full ARN of MFA Device the code is from"
    ),
    auth_token: str = typer.Argument(
        ..., help="6 digit 2 factor authentication code from the MFA device"
    ),
):
    """
    Exec into a shell with appropriate AWS credentials (including MFA)
    """
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

    env = os.environ | {
        "AWS_ACCESS_KEY_ID": creds["Credentials"]["AccessKeyId"],
        "AWS_SECRET_ACCESS_KEY": creds["Credentials"]["SecretAccessKey"],
        "AWS_SESSION_TOKEN": creds["Credentials"]["SessionToken"],
        "AWS_PROFILE": profile,
    }

    subprocess.check_call([os.environ["SHELL"], "-l"], env=env)
