"""
Commands for reserving placeholders
"""

from typing import Literal

import typer
from ruamel.yaml import YAML

from deployer.dev.app import generate_app
from deployer.infra_components.cluster import Cluster

yaml = YAML(typ="rt", pure=True)


@generate_app.command()
def user_replicas(
    cluster_name: str = typer.Argument(
        "2i2c",
        help="Name of cluster for which to reserve capacity",
    ),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    replicas: int = typer.Argument(...),
):
    """
    Scale up user placeholders to reserve capacity via N user placeholders
    """
    patch_replicas(cluster_name, hub_name, replicas, "user")


@generate_app.command()
def node_replicas(
    cluster_name: str = typer.Argument(
        "2i2c",
        help="Name of cluster for which to reserve capacity",
    ),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    replicas: int = typer.Argument(...),
):
    """
    Scale up node placeholders to reserve capacity via N node placeholders
    """
    patch_replicas(cluster_name, hub_name, replicas, "node")


def patch_replicas(
    cluster_name: str,
    hub_name: str,
    replicas: int,
    kind: Literal["node", "user"],
):
    cluster = Cluster.from_name(cluster_name)

    if replicas < 0:
        raise ValueError(f"Replicas must not be less than zero: {replicas}")

    # Make sure that hub exists!
    try:
        next(h for h in cluster.hubs if h.spec["name"] == hub_name)
    except StopIteration:
        raise ValueError(f"No hub with name {hub_name} found in {cluster_name} cluster")

    # Expect <hub_name>.values.yaml. We could also look for `<hub_name>-placeholders.values.yaml` for a more systematic approach
    # This expectation meanwhile imposes constraints on hub value file names.
    expected_config_path = cluster.config_dir / f"{hub_name}.values.yaml"
    if not expected_config_path.exists():
        raise FileNotFoundError(
            f"Could not find values file for {hub_name} hub in expected location ({expected_config_path})"
        )

    hub_config = yaml.load(expected_config_path)
    basehub_config = hub_config.get("basehub", hub_config)

    try:
        if kind == "node":
            placeholders = basehub_config["nodePlaceholder"]
        else:
            placeholders = basehub_config["jupyterhub"]["scheduling"]["userPlaceholder"]
    except KeyError as exc:
        exc.add_note(f"Could not find {kind} placeholders section in hub configuration")
        raise

    # Scale repliacs
    placeholders["replicas"] = replicas

    yaml.dump(hub_config, expected_config_path)
