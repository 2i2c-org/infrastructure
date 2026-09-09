"""
Creates a new typer application, which is then
nested as a sub-command named "get"
under the `config` sub-command of the deployer.
"""

import typer

from deployer.dev.app import config_app

get_app = typer.Typer(pretty_exceptions_show_locals=False)
config_app.add_typer(
    get_app,
    name="get",
    help="Retrieve various info from the configuration files",
)
