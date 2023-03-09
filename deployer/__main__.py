# Import the various subcommands here, they will be automatically
# registered into the app
import deployer.cilogon_app  # noqa: F401
import deployer.debug  # noqa: F401
import deployer.deployer  # noqa: F401
import deployer.generate.generate_aws_cluster  # noqa: F401
import deployer.generate.generate_gcp_cluster  # noqa: F401
import deployer.grafana.central_grafana  # noqa: F401
import deployer.grafana.grafana_tokens  # noqa: F401
import deployer.keys.decrypt_age  # noqa: F401

from .cli_app import app


def main():
    app()
