"""
Creates a new typer application, which is then
nested as a sub-command named "hub-asset"
under the `generate` sub-command of the deployer.
"""

import typer

from deployer.cli_app import generate_app

hub_asset_app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app.add_typer(
    hub_asset_app,
    name="hub-asset",
    help="Generate various hub assets to make deploying a new hub easier",
)
