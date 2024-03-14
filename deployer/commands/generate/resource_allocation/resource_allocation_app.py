"""
Creates a new typer application, which is then
nested as a sub-command named "resource-allocation"
under the `generate` sub-command of the deployer.
"""

import typer

from deployer.cli_app import generate_app

resource_allocation_app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app.add_typer(
    resource_allocation_app,
    name="resource-allocation",
    help="Generate the choices for a resource allocation strategy of an instance type and additional helper information",
)
