"""
Export the typer apps we use throughout our codebase.

Having this in a single file allows multiple files to provide subcommands
for the same CLI application. So we can put deployment related stuff under
deployer.py, debug related stuff under debug.py, etc
"""

import typer

# The typer app to which all subcommands are attached
# Disable 'pretty' exception handling
app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app = typer.Typer(pretty_exceptions_show_locals=False)
config_app = typer.Typer(pretty_exceptions_show_locals=False)
cilogon_client_app = typer.Typer(pretty_exceptions_show_locals=False)
debug_app = typer.Typer(pretty_exceptions_show_locals=False)
exec_app = typer.Typer(pretty_exceptions_show_locals=False)
grafana_app = typer.Typer(pretty_exceptions_show_locals=False)
validate_app = typer.Typer(pretty_exceptions_show_locals=False)
transform_app = typer.Typer(pretty_exceptions_show_locals=False)
verify_backups_app = typer.Typer(pretty_exceptions_show_locals=False)
update_app = typer.Typer(pretty_exceptions_show_locals=False)

app.add_typer(
    generate_app,
    name="generate",
    help="Generate various types of assets. It currently supports generating files related to billing, "
    "new dedicated clusters, helm upgrade strategies and resource allocation.",
)
app.add_typer(
    config_app,
    name="config",
    help="Get refined information from the config folder.",
)
app.add_typer(
    cilogon_client_app,
    name="cilogon-client",
    help="Manage cilogon clients for hubs' authentication.",
)
app.add_typer(
    exec_app,
    name="exec",
    help="Execute a shell in various parts of the infra. It can be used for poking around, or debugging issues.",
)
app.add_typer(
    debug_app,
    name="debug",
    help="Debug issues by accessing different components and their logs",
)
app.add_typer(grafana_app, name="grafana", help="Manages Grafana related workflows.")
app.add_typer(
    validate_app,
    name="validate",
    help="Validate configuration files such as helm chart values and cluster.yaml files.",
)
app.add_typer(
    transform_app,
    name="transform",
    help="Programmatically transform datasets, such as cost tables for billing purposes.",
)
app.add_typer(
    update_app,
    name="update",
    help="Update existing resources, such as clusters or configurations.",
)
app.add_typer(
    verify_backups_app,
    name="verify-backups",
    help="Verify backups of home directories have been successfully created, and old backups have been cleared out.",
)
