import typer

from deployer.app import app

# Category for local developmen tools
DEVELOPMENT = "Development"


generate_app = typer.Typer(pretty_exceptions_show_locals=False)
config_app = typer.Typer(pretty_exceptions_show_locals=False)
cilogon_client_app = typer.Typer(pretty_exceptions_show_locals=False)
debug_app = typer.Typer(pretty_exceptions_show_locals=False)
exec_app = typer.Typer(pretty_exceptions_show_locals=False)
grafana_app = typer.Typer(pretty_exceptions_show_locals=False)
transform_app = typer.Typer(pretty_exceptions_show_locals=False)
update_app = typer.Typer(pretty_exceptions_show_locals=False)
app.add_typer(
    generate_app,
    name="generate",
    help="Generate various types of assets & information",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    config_app,
    name="config",
    help="Get refined information from the config folder.",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    cilogon_client_app,
    name="cilogon-client",
    help="Manage cilogon clients for hubs' authentication.",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    exec_app,
    name="exec",
    help="Execute a shell in various parts of the infra. It can be used for poking around, or debugging issues.",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    debug_app,
    name="debug",
    help="Debug issues by accessing different components and their logs",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    grafana_app,
    name="grafana",
    help="Manages Grafana related workflows.",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    transform_app,
    name="transform",
    help="Programmatically transform datasets, such as cost tables for billing purposes.",
    rich_help_panel=DEVELOPMENT,
)
app.add_typer(
    update_app,
    name="update",
    help="Update existing resources, such as clusters or configurations.",
    rich_help_panel=DEVELOPMENT,
)
