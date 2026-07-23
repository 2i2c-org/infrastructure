"""
Export the typer apps we use throughout our codebase.

Having this in a single file allows multiple files to provide subcommands
for the same CLI application. So we can put deployment related stuff under
deployer.py, debug related stuff under debug.py, etc
"""

import typer

# Category for tools that are required in CI/CD
CONTINUOUS_DEPLOYMENT = "Continuous Deployment"
# The typer app to which all subcommands are attached
# Disable 'pretty' exception handling
app = typer.Typer(rich_markup_mode="markdown", pretty_exceptions_show_locals=False)
validate_app = typer.Typer(pretty_exceptions_show_locals=False)

app.add_typer(
    validate_app,
    name="validate",
    help="Validate configuration files such as helm chart values and cluster.yaml files.",
    rich_help_panel=CONTINUOUS_DEPLOYMENT,
)
