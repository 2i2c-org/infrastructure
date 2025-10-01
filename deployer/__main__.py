# Import the various subcommands here, they will be automatically
# registered into the app
import deployer.commands.deploy_dashboards  # noqa: F401
import deployer.commands.deployer  # noqa: F
import deployer.commands.plan_upgrade.jobs  # noqa: F401
import deployer.commands.validate.config  # noqa: F401401
import deployer.dev_commands.cilogon  # noqa: F401
import deployer.dev_commands.config.get_clusters  # noqa: F401
import deployer.dev_commands.debug  # noqa: F401
import deployer.dev_commands.develop.use_cluster_credentials  # noqa: F401
import deployer.dev_commands.exec.aws.aws_app  # noqa: F401
import deployer.dev_commands.exec.infra_components  # noqa: F401
import deployer.dev_commands.exec.promql  # noqa: F401
import deployer.dev_commands.generate.billing.cost_table  # noqa: F401
import deployer.dev_commands.generate.cryptnono_config  # noqa: F401
import deployer.dev_commands.generate.dedicated_cluster.aws  # noqa: F401
import deployer.dev_commands.generate.dedicated_cluster.gcp  # noqa: F401
import deployer.dev_commands.generate.hub_asset.cluster_entry  # noqa: F401
import deployer.dev_commands.generate.hub_asset.hub_files  # noqa: F401
import deployer.dev_commands.generate.resource_allocation.daemonset_requests  # noqa: F401
import deployer.dev_commands.generate.resource_allocation.generate_choices  # noqa: F401
import deployer.dev_commands.generate.resource_allocation.instance_capacities  # noqa: F401
import deployer.dev_commands.generate.resource_allocation.update_nodeinfo  # noqa: F401
import deployer.dev_commands.grafana.central_grafana  # noqa: F401
import deployer.dev_commands.grafana.tokens  # noqa: F401
import deployer.dev_commands.keys.decrypt_age  # noqa: F401
import deployer.dev_commands.transform.cost_table  # noqa: F401
import deployer.dev_commands.update.eksctl  # noqa: F401
import deployer.dev_commands.verify_backups  # noqa: F401

from .cli_app import app
from .utils.jsonnet import validate_jsonnet_version


def main():
    validate_jsonnet_version()
    app()
