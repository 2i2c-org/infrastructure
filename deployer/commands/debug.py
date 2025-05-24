"""
Helper commands for debugging active issues in a hub
"""

import string
import subprocess
from enum import Enum

import escapism
import typer
from ruamel.yaml import YAML

from deployer.cli_app import debug_app
from deployer.infra_components.cluster import Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


class InfraComponents(Enum):
    """
    Enum of various components that make up a particular hub's infrastructure
    """

    hub = "hub"
    proxy = "proxy"
    dask_gateway_api = "dask-gateway-api"
    dask_gateway_controller = "dask-gateway-controller"
    dask_gateway_traefik = "dask-gateway-traefik"


@debug_app.command()
def component_logs(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    component: InfraComponents = typer.Argument(
        ..., help="Component to display logs of"
    ),
    follow: bool = typer.Option(True, help="Live update new logs as they show up"),
    previous: bool = typer.Option(
        False,
        help="If component pod has restarted, show logs from just before the restart",
    ),
):
    """
    Display logs from a particular component on a hub on a cluster
    """

    # hub_name is also the name of the namespace the hub is in
    cmd = ["kubectl", "-n", hub_name, "logs"]

    component_map = {
        "hub": ["-l", "component=hub", "-c", "hub"],
        "proxy": ["-l", "component=proxy"],
        "dask-gateway-api": ["-l", "app.kubernetes.io/component=gateway"],
        "dask-gateway-controller": ["-l", "app.kubernetes.io/component=controller"],
        "dask-gateway-traefik": ["-l", "app.kubernetes.io/component=traefik"],
    }

    cmd += component_map[component.value]

    if follow:
        cmd += ["-f"]
    if previous:
        cmd += ["--previous"]

    cluster = Cluster.from_name(cluster_name)

    with cluster.auth():
        subprocess.check_call(cmd)


@debug_app.command()
def user_logs(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    username: str = typer.Argument(
        ..., help="Name of the JupyterHub user to get logs for"
    ),
    follow: bool = typer.Option(True, help="Live update new logs as they show up"),
    previous: bool = typer.Option(
        False,
        help="If user pod has restarted, show logs from just before the restart",
    ),
):
    """
    Display logs from the notebook pod of a given user
    """
    # This is how kubespawner determines the 'safe' username, which is
    # used in the label. Kubernetes restricts what characters can be in
    # the label value.

    # Note: '-' is not in safe_chars, as it is being used as escape character
    safe_chars = set(string.ascii_lowercase + string.digits)
    escaped_username = escapism.escape(
        username, safe=safe_chars, escape_char="-"
    ).lower()

    cmd = [
        "kubectl",
        "-n",
        hub_name,
        "logs",
        "-l",
        f"hub.jupyter.org/username={escaped_username}",
        "-c",
        "notebook",
    ]

    if follow:
        cmd += ["-f"]
    if previous:
        cmd += ["--previous"]
    cluster = Cluster.from_name(cluster_name)
    with cluster.auth():
        # hub_name is also the name of the namespace the hub is in
        subprocess.check_call(cmd)


@debug_app.command()
def start_docker_proxy(
    docker_daemon_cluster: str = typer.Argument(
        "2i2c", help="Name of cluster where the docker daemon lives"
    )
):
    """
    Proxy a docker daemon from a remote cluster to local port 23760.
    """

    print(
        "Run `export DOCKER_HOST=tcp://localhost:23760` on another terminal to use the remote docker daemon"
    )
    cluster = Cluster.from_name(docker_daemon_cluster)
    with cluster.auth():
        cmd = [
            "kubectl",
            "--namespace=default",
            "port-forward",
            "deployment/dind",
            "23760:2376",
        ]

        subprocess.check_call(cmd)
