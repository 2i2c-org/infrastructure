"""
Creates a new typer application, which is then
nested as a sub-command named "resource-allocation"
under the `generate` sub-command of the deployer.
"""

import typer

from deployer.dev.app import generate_app

progress_matrix_app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app.add_typer(
    progress_matrix_app,
    name="progress-matrix",
    help="Generate the progress of various batched deployments",
)
