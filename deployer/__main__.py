# Import the various subcommands here, they will be automatically
# registered into the app
import deployer.central_grafana  # noqa: F401
import deployer.debug  # noqa: F401
import deployer.deployer  # noqa: F401
import deployer.generate_aws_cluster  # noqa: F401
import deployer.generate_gcp_cluster  # noqa: F401

from .cli_app import app


def main():
    app()
