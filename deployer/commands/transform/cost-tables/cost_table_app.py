"""
Creates a new typer application, which is then nested as a sub-command named
"cost-table" under the `transform` sub-command of the deployer.
"""

import typer

from deployer.cli_app import transform_app

cost_table_app = typer.Typer(pretty_exceptions_show_locals=False)
transform_app.add_typer(
    cost_table_app,
    name="cost-table",
    help="Transform the cost table from a cloud provider when completing billing cycles"
)
