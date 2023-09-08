# Import the various subcommands here, they will be automatically
# registered into the app
import deployer.commands.cilogon_client_cmd  # noqa: F401
import deployer.commands.deployer  # noqa: F401
import deployer.commands.exec.debug_app_and_commands  # noqa: F401
import deployer.commands.exec.shell.cloud_commands  # noqa: F401
import deployer.commands.exec.shell.infra_components_commands  # noqa: F401
import deployer.commands.generate.billing.cost_table_cmd  # noqa: F401
import deployer.commands.generate.dedicated_cluster.aws_commands  # noqa: F401
import deployer.commands.generate.dedicated_cluster.gcp_commands  # noqa: F401
import deployer.commands.generate.helm_upgrade.jobs_cmd  # noqa: F401
import deployer.commands.grafana.central_grafana  # noqa: F401
import deployer.commands.grafana.deploy_dashboards_cmd  # noqa: F401
import deployer.commands.grafana.tokens_cmd  # noqa: F401
import deployer.commands.validate.config_cmd  # noqa: F401
import deployer.keys.decrypt_age  # noqa: F401

from .cli_app import app


def main():
    app()
