import os

import typer
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    CONFIG_CLUSTERS_PATH,
    HELM_CHARTS_DIR,
    REPO_ROOT_PATH,
)

from .progress_matrix_app import progress_matrix_app

yaml = YAML(typ="safe", pure=True)

console = Console()


def determine_dask_z2jh_version(chart_file):
    # Function to determine what z2jh version
    # a hub is deploying
    with open(chart_file, "r+") as f:
        config = yaml.load(f)
        for dep in config["dependencies"]:
            if dep["name"] == "jupyterhub":
                return dep["version"]


def get_chart_yaml_filepath(hub):
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


def turn_data_into_table(title, columns, highlight_idx, threshold, data):
    table = Table(title=title, header_style="bold cyan")

    for idx, col in enumerate(columns):
        if idx != highlight_idx:
            table.add_column(col, style="white", no_wrap=True)
        else:
            table.add_column(col, style="green", justify="right")

    for cluster, hubs in sorted(data.items()):
        for hub, version in sorted(hubs.items()):
            version_style = "bold yellow" if version != threshold else "green"
            table.add_row(cluster, hub, f"[{version_style}]{version}[/]")

    return table


@progress_matrix_app.command()
def get_z2jh_version(
    cluster_name: str = typer.Argument(None, help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        None,
        help="Name of hub to operate deploy. Omit to deploy all hubs on the cluster",
    ),
    threshold: str = typer.Option(
        None,
        help="Versions different than this will be highlighted",
    ),
):
    clusters = os.listdir(CONFIG_CLUSTERS_PATH)
    if cluster_name:
        clusters = [cluster_name]
    z2jh_version = {}

    for c_name in clusters:
        try:
            z2jh_version[c_name] = {}
            cluster = Cluster.from_name(c_name)
            hubs = cluster.hubs
            if hub_name:
                hubs = [h for h in cluster.hubs if h.spec["name"] in hub_name]

            for hub in hubs:
                z2jh_version[c_name][hub.spec["name"]] = determine_dask_z2jh_version(
                    get_chart_yaml_filepath(hub)
                )
        except FileNotFoundError:
            continue

    columns = ["Cluster", "Hub", "Z2JH version"]
    table = turn_data_into_table(
        title="Z2JH versions",
        columns=columns,
        highlight_idx=3,
        threshold=threshold,
        data=z2jh_version,
    )

    console.print(table)
    return z2jh_version
