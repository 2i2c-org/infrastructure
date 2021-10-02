import nox

nox.options.reuse_existing_virtualenvs = True

BUILD_COMMAND = ["-b", "html", "docs", "docs/_build/html"]

def install_deps(session):
    # Manually installing this because conda is a bit wonky w/ nox
    session.conda_install("--channel=conda-forge", "go-terraform-docs", "python=3.8")
    session.install("-r", "docs/requirements.txt")

@nox.session(venv_backend='conda')
def docs(session):
    install_deps(session)
    session.run("sphinx-build", *BUILD_COMMAND)

@nox.session(venv_backend='conda')
@nox.session
def docs_live(session):
    install_deps(session)

    cmd = ["sphinx-autobuild"]
    for path in ["*/_build/*", "*/tmp/*", "*/reference/terraform.md"]:
        cmd.extend(['--ignore', path])
    cmd.extend(BUILD_COMMAND)
    session.run(*cmd)