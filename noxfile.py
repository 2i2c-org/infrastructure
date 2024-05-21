"""
noxfile.py is a configuration file for the command-line tool nox that automates
tasks in multiple Python environments. We use it to setup an environment to
build our documentation.

Config reference: https://nox.thea.codes/en/stable/config.html#noxfile

Common tasks:
- Install nox:                        pip install nox
- Start a live reloading docs server: nox -- live
"""

import nox

nox.options.reuse_existing_virtualenvs = True

BUILD_COMMAND = ["-b", "dirhtml", "docs", "docs/_build/dirhtml"]


@nox.session(venv_backend="conda")
def docs(session):
    """Build the documentation. Use `-- live` for a live server to preview changes."""
    session.install("-r", "docs/requirements.txt")

    if "live" in session.posargs:
        session.posargs.pop(session.posargs.index("live"))

        # Add folders to ignore
        # keep this in sync with Makefile
        AUTOBUILD_IGNORE_DIRS = [
            "_build",
            "tmp",
        ]
        # Add files to ignore
        # keep this in sync with Makefile
        AUTOBUILD_IGNORE_FILES = [
            "*.json",
            "*.csv",
        ]

        cmd = ["sphinx-autobuild"]
        for folder in AUTOBUILD_IGNORE_DIRS:
            cmd.extend(["--ignore", f"*/{folder}/*"])
        for file in AUTOBUILD_IGNORE_FILES:
            cmd.extend(["--ignore", f"*/{file}"])

        # Find an open port to serve on
        cmd.extend(["--port", "0"])

    else:
        cmd = ["sphinx-build"]

    cmd.extend(BUILD_COMMAND + session.posargs)
    session.run(*cmd)
