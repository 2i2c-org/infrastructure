import os

import typer
from ruamel.yaml import YAML

from deployer.cli_app import config_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import get_all_cluster_yaml_files

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@config_app.command()
def get_clusters(
    provider: str = typer.Option(
        "", help="(Optional) Filter results to clusters with this provider specified."
    ),
):
    """
    Prints all cluster names sorted alphabetically, optionally filtered by the
    'provider' field in the cluster.yaml file.
    """
    cluster_names = []
    for config_file_path in get_all_cluster_yaml_files():
        with open(config_file_path) as f:
            cluster = Cluster(yaml.load(f), config_file_path.parent)
        if provider and cluster.spec["provider"] != provider:
            continue
        cluster_names.append(os.path.basename(config_file_path.parent))

    cluster_names = sorted(cluster_names)
    for cn in cluster_names:
        print(cn)
