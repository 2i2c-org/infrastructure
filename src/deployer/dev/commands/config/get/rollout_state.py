import json

import typer
from rich.console import Console
from ruamel.yaml import YAML

from deployer.dev.commands.config.get.k8s_version import compute_k8s_versions
from deployer.dev.commands.config.get.subchart_version import compute_z2jh_versions
from deployer.dev.commands.config.get.utils import (
    merge_version_dicts,
    render_versions_table,
)

from .app import get_app

yaml = YAML(typ="safe", pure=True)
console = Console()


@get_app.command()
def rollout_state(
    cluster_name: str = typer.Argument(
        None,
        help="Name of cluster to operate on.",
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Output as JSON instead of table"
    ),
):
    k8s_versions = compute_k8s_versions(cluster_name=cluster_name)
    z2jh_versions = compute_z2jh_versions(cluster_name=cluster_name)

    data = merge_version_dicts(
        k8s_versions, z2jh_versions, metric_names=["k8s", "z2jh"]
    )

    if as_json:
        data = json.dumps(data, indent=2)
        typer.echo(data)

    table = render_versions_table(data)
    console.print(table)
    return json.dumps(data, indent=2)
