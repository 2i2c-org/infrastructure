# Import the various subcommands here, they will be automatically
# registered into the app
import deployer.commands.cilogon  # noqa: F401
import deployer.commands.config.get_clusters  # noqa: F401
import deployer.commands.debug  # noqa: F401
import deployer.commands.deployer  # noqa: F401
import deployer.commands.exec.cloud  # noqa: F401
import deployer.commands.exec.infra_components  # noqa: F401
import deployer.commands.generate.billing.cost_table  # noqa: F401
import deployer.commands.generate.cryptnono_config  # noqa: F401
import deployer.commands.generate.dedicated_cluster.aws  # noqa: F401
import deployer.commands.generate.dedicated_cluster.gcp  # noqa: F401
import deployer.commands.generate.helm_upgrade.jobs  # noqa: F401
import deployer.commands.generate.hub_asset.cluster_entry  # noqa: F401
import deployer.commands.generate.hub_asset.hub_files  # noqa: F401
import deployer.commands.generate.resource_allocation.daemonset_requests  # noqa: F401
import deployer.commands.generate.resource_allocation.generate_choices  # noqa: F401
import deployer.commands.generate.resource_allocation.instance_capacities  # noqa: F401
import deployer.commands.generate.resource_allocation.update_nodeinfo  # noqa: F401
import deployer.commands.grafana.central_grafana  # noqa: F401
import deployer.commands.grafana.deploy_dashboards  # noqa: F401
import deployer.commands.grafana.tokens  # noqa: F401
import deployer.commands.transform.cost_table  # noqa: F401
import deployer.commands.validate.config  # noqa: F401
import deployer.commands.verify_backups  # noqa: F401
import deployer.keys.decrypt_age  # noqa: F401

from .cli_app import app
from .utils.jsonnet import validate_jsonnet_version


def main():
    validate_jsonnet_version()
    app()
