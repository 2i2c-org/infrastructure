"""
Creates a new typer application, which is then
nested as a sub-command named "az"
under the `exec` sub-command of the deployer.

Helper methods for commandline access to Azure.
"""

import subprocess
from typing import Annotated

import typer

from deployer.cli_app import exec_app

az = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(
    az,
    name="az",
    help="Helper methods for commandline access to Azure.",
)


@az.command(context_settings={"allow_extra_args": True})
def with_storage_rule(
    ctx: typer.Context,
    account_name: Annotated[str, typer.Argument(help="Storage account name")],
    ip_address: Annotated[str, typer.Argument(help="IPv4 address/CIDR range")],
):
    """
    Execute a command within the context of a network storage rule for Azure
    """
    subprocess.check_call(
        [
            "az",
            "storage",
            "account",
            "network-rule",
            "add",
            "--account-name",
            account_name,
            "--ip-address",
            ip_address,
        ]
    )
    try:
        subprocess.check_call(ctx.args)
    finally:
        subprocess.check_call(
            [
                "az",
                "storage",
                "account",
                "network-rule",
                "remove",
                "--account-name",
                account_name,
                "--ip-address",
                ip_address,
            ]
        )
