"""
Creates a new typer application, which is then
nested as a sub-command named "shell"
under the `exec` sub-command of the deployer.
"""
import typer

from ....cli_app import exec_app

exec_shell_app = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(exec_shell_app, name="shell")
