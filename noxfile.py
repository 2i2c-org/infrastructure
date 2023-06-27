import nox

nox.options.reuse_existing_virtualenvs = True

BUILD_COMMAND = ["-b", "html", "docs", "docs/_build/html"]


def install_deps(session):
    session.install("-r", "docs/requirements.txt")


@nox.session(venv_backend="conda")
def docs(session):
    install_deps(session)
    session.run("sphinx-build", *BUILD_COMMAND)


@nox.session(name="docs-live", venv_backend="conda")
def docs_live(session):
    install_deps(session)

    cmd = ["sphinx-autobuild"]
    for path in ["*/_build/*", "*/tmp/*"]:
        cmd.extend(["--ignore", path])
    cmd.extend(BUILD_COMMAND)
    session.run(*cmd)
