"""
Export the typer app we use throughout our codebase.

Having this in a single file allows multiple files to provide subcommands
for the same CLI application. So we can put deployment related stuff under
deployer.py, debug related stuff under debug.py, etc
"""
import typer

# The typer app to which all subcommands are attached
# Disable 'pretty' exception handling
app = typer.Typer(pretty_exceptions_show_locals=False)
generate_app = typer.Typer(pretty_exceptions_show_locals=False)
cilogon_client_app = typer.Typer(pretty_exceptions_show_locals=False)

app.add_typer(generate_app, name="generate")
app.add_typer(cilogon_client_app, name="cilogon-client")
