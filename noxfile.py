"""
noxfile.py is a configuration file for the command-line tool nox that automates
tasks in multiple Python environments. We use it to setup an environment to
build our documentation.

Config reference: https://nox.thea.codes/en/stable/config.html#noxfile

Common tasks:
- Install nox:                        pip install nox
- List commands to run:               nox -l
- Run a command                       nox -s <command>
"""

import nox

nox.options.reuse_existing_virtualenvs = True


def _setup(session):
    """Install dependencies and generate the hub tables, then cd into docs/."""
    session.install("-r", "docs/requirements.txt")
    # Let mystmd install its own Node.js (via nodeenv) without prompting
    session.env["MYSTMD_ALLOW_NODEENV"] = "1"
    session.chdir("docs")
    # Generate the hub tables that reference/hubs.md includes
    session.run("python", "-m", "helper_programs.hub_info_table")


@nox.session()
def docs(session):
    """Build the documentation."""
    _setup(session)
    session.run("myst", "build", "--execute", "--html", *session.posargs)


# Supporting docs-live is for historical reasons...docs:live is more consistent w/ JS
# workflows but historically it has been docs-live.
# We can probably remove the docs-live pattern after 2027-01-01.
@nox.session(name="docs-live")
@nox.session(name="docs:live")
def docs_live(session):
    """Start a live server to preview changes to the documentation."""
    _setup(session)
    session.run("myst", "start", "--execute", *session.posargs)
