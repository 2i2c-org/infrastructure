import typer

from ...cli_app import exec_app

exec_shell_app = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(exec_shell_app, name="shell")
