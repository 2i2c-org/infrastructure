# Import the various subcommands here, they will be automatically
# registered into the app

import os

from . import commands  # noqa: F401
from .app import app
from .utils.jsonnet import validate_jsonnet_version

# Set up a smaller deployer in CI
if not ("DEPLOYER_ONLY_CORE" in os.environ or "GITHUB_WORKSPACE" in os.environ):
    from .dev import commands as dev_commands  # noqa: F401


def main():
    validate_jsonnet_version()
    app()
