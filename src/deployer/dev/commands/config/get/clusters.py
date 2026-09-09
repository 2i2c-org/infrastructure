import os

import typer
from ruamel.yaml import YAML

from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import get_all_cluster_yaml_files

from .app import get_app

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@get_app.command()
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
            cluster = Cluster(yaml.load(f), config_file_path)
        if provider and cluster.spec["provider"] != provider:
            continue
        cluster_names.append(os.path.basename(config_file_path.parent))

    cluster_names = sorted(cluster_names)
    for cn in cluster_names:
        print(cn)


@get_app.command()
def get(values_files_list, config_dir, config_key, legacy_daskhub):
    # config_key is of form "jupyterhub.hub.config"
    keys = config_key.split(".")

    for values_file_name in values_files_list:
        if "secret" not in os.path.basename(values_file_name):
            values_file = config_dir / values_file_name
            config = yaml.load(values_file)
            if legacy_daskhub:
                config = config.get("basehub", {})

            for key in keys:
                new_config = config.get(key, {})
                config = new_config

            return config
