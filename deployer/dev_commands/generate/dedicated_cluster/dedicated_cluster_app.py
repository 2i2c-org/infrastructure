"""
Creates a new typer application, which is then
nested as a sub-command named "dedicated-cluster"
under the `generate` sub-command of the deployer.
"""

import typer

from deployer.cli_app import generate_app

dedicated_cluster_app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app.add_typer(
    dedicated_cluster_app,
    name="dedicated-cluster",
    help="Generate the initial files needed for a new cluster on GCP or AWS.",
)
