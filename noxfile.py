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
        AUTOBUILD_IGNORE = [
            "_build",
            "tmp",
        ]

        cmd = ["sphinx-autobuild"]
        for folder in AUTOBUILD_IGNORE:
            cmd.extend(["--ignore", f"*/{folder}/*"])

        # Find an open port to serve on
        cmd.extend(["--port", "0"])

    else:
        cmd = ["sphinx-build"]

    cmd.extend(BUILD_COMMAND + session.posargs)
    session.run(*cmd)
