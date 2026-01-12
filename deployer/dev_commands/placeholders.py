"""
Commands for reserving placeholders
"""

import typer
from ruamel.yaml import YAML

from deployer.cli_app import placeholders_app
from deployer.infra_components.cluster import Cluster

yaml = YAML(typ="rt", pure=True)


@placeholders_app.command()
def reserve(
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
        placeholders = basehub_config["jupyterhub"]["scheduling"]["userPlaceholder"]
    except KeyError as exc:
        exc.add_note("Could not find userPlaceholders section in hub configuration")
        raise

    # Scale repliacs
    placeholders["replicas"] = replicas

    yaml.dump(hub_config, expected_config_path)
