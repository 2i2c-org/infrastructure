import os
from pathlib import Path

import typer
from rich.console import Console
from ruamel.yaml import YAML

from deployer.dev.commands.config.get.utils import (
    turn_data_into_table,
)
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    CONFIG_CLUSTERS_PATH,
    HELM_CHARTS_DIR,
    REPO_ROOT_PATH,
)

from .app import get_app

yaml = YAML(typ="safe", pure=True)
console = Console()


def determine_dask_z2jh_version(chart_file: Path) -> str | None:
    # Function to determine what z2jh version
    # a hub is deploying
    with open(chart_file, "r+") as f:
        config = yaml.load(f)
        for dep in config["dependencies"]:
            if dep.get("name", "") == "jupyterhub":
                return dep.get("version")


def get_chart_yaml_filepath(hub) -> Path | None:
    chart_override = hub.spec.get("chart_override", None)
    if chart_override:
        if "/" in chart_override:
            # It's probably a path relative to the repo root
            chart_override_path = REPO_ROOT_PATH / chart_override
            chart_override = chart_override.split("/")[-1]
        else:
            chart_override_path = (
                hub.cluster.config_dir / chart_override if chart_override else None
            )
    else:
        chart_override_path = HELM_CHARTS_DIR / "basehub/Chart.yaml"

    return chart_override_path


def compute_z2jh_versions(
    cluster_name: str | None = None,
    hub_name: str | None = None,
) -> dict:
    """
    Compute Z2JH versions for clusters/hubs.

    - If cluster_name is None, all clusters are processed.
    - If hub_name is None, all hubs on each cluster are processed.
    - If hub_name is provided, only hubs with that exact name are included.
    """
    clusters = os.listdir(CONFIG_CLUSTERS_PATH)
    if cluster_name:
        clusters = [cluster_name]
    z2jh_versions = {}

    for c_name in clusters:
        try:
            z2jh_versions[c_name] = {}
            cluster = Cluster.from_name(c_name)
            hubs = cluster.hubs
            if hub_name:
                hubs = [h for h in cluster.hubs if h.spec["name"] in hub_name]

            for hub in hubs:
                z2jh_versions[c_name][hub.spec["name"]] = determine_dask_z2jh_version(
                    get_chart_yaml_filepath(hub)
                )
        except FileNotFoundError:
            continue
    return z2jh_versions


@get_app.command()
def z2jh_version(
    cluster_name: str = typer.Argument(
        None,
        help="Name of cluster to operate on. If left empty will run for all clusters.",
    ),
    hub_name: str = typer.Argument(
        None,
        help="Name of hub to operate deploy. Omit to deploy all hubs on the cluster",
    ),
    threshold: str = typer.Option(
        None,
        help="Versions different than this will be highlighted",
    ),
) -> dict:
    z2jh_versions = compute_z2jh_versions(cluster_name, hub_name)

    columns = ["Cluster", "Hub", "Z2JH version"]
    table = turn_data_into_table(
        title="Z2JH versions",
        columns=columns,
        highlight_idx=3,
        threshold=threshold,
        data=z2jh_versions,
    )

    console.print(table)
    return z2jh_version
