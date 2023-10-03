"""
Helper commands for debugging active issues in a hub
"""
import json
import string
import subprocess
from enum import Enum

import escapism
import typer
from ruamel.yaml import YAML

from .cli_app import app
from .cluster import Cluster
from .file_acquisition import find_absolute_path_to_cluster_file
from .utils import print_colour

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


@app.command()
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
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        subprocess.check_call(cmd)


@app.command()
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
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        # hub_name is also the name of the namespace the hub is in
        subprocess.check_call(cmd)


@app.command()
def exec_homes_shell(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
):
    """
    Pop an interactive shell with the home directories of the given hub mounted on /home
    """
    # Name pod to include hub name so it is displayed as part of the default prompt
    # This makes sure we don't end up deleting the wrong thing
    pod_name = f"{cluster_name}-{hub_name}-shell"
    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "spec": {
            "terminationGracePeriodSeconds": 1,
            "automountServiceAccountToken": False,
            "volumes": [
                # This PVC is created by basehub
                {"name": "home", "persistentVolumeClaim": {"claimName": "home-nfs"}}
            ],
            "containers": [
                {
                    "name": pod_name,
                    # Use ubuntu image so we get better gnu rm
                    "image": "ubuntu:jammy",
                    "stdin": True,
                    "stdinOnce": True,
                    "tty": True,
                    "volumeMounts": [
                        {
                            "name": "home",
                            "mountPath": "/home",
                        }
                    ],
                }
            ],
        },
    }

    cmd = [
        "kubectl",
        "-n",
        hub_name,
        "run",
        "--rm",  # Remove pod when we're done
        "-it",  # Give us a shell!
        "--overrides",
        json.dumps(pod),
        "--image",
        # Use ubuntu image so we get GNU rm and other tools
        # Should match what we have in our pod definition
        "ubuntu:jammy",
        pod_name,
        "--",
        "/bin/bash",
        "-l",
    ]

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        subprocess.check_call(cmd)


@app.command()
def exec_hub_shell(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
):
    """
    Pop an interactive shell in the hub pod
    """
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        pod_name = (
            subprocess.check_output(
                [
                    "kubectl",
                    "-n",
                    hub_name,
                    "get",
                    "pod",
                    "-o",
                    "name",
                    "-l",
                    "component=hub",
                ]
            )
            .decode()
            .strip()
        )
        cmd = [
            "kubectl",
            "-n",
            hub_name,
            "exec",
            "-it",  # Give us an interactive shell!
            pod_name,
            "-c",
            "hub",
            "--",
            "/bin/bash",
            "-l",
        ]
        subprocess.check_call(cmd)


@app.command()
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
    config_file_path = find_absolute_path_to_cluster_file(docker_daemon_cluster)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        cmd = [
            "kubectl",
            "--namespace=default",
            "port-forward",
            "deployment/dind",
            "23760:2376",
        ]

        subprocess.check_call(cmd)


@app.command()
def transfer_old_home_dir_to_new_location(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    source_user: str = typer.Option(
        prompt=True,
        confirmation_prompt=True,
        help="Name of source user who's home dir files we are transferring",
    ),
    destination_user: str = typer.Option(
        prompt=True,
        confirmation_prompt=True,
        help="Name of destination user to whose home dir we will be moving the files",
    ),
):
    """
    Copy all the files from a user's home dir to a subdir in destination user's home dir
    """
    # Name the pod so we know what to delete when the transfer is done
    pod_name = f"{cluster_name}-{hub_name}-transfer-shell"
    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "spec": {
            "terminationGracePeriodSeconds": 1,
            "automountServiceAccountToken": False,
            # Make sure the pod and containers can only be ran as the jupyter user
            # Otherwise the files we copy might end up be owned by another user
            "securityContext": {"runAsUser": 1000, "runAsGroup": 1000},
            "volumes": [
                # This PVC is created by basehub
                {"name": "home", "persistentVolumeClaim": {"claimName": "home-nfs"}}
            ],
            "containers": [
                {
                    "name": pod_name,
                    # Use ubuntu image so we get better GNU cp
                    "image": "ubuntu:jammy",
                    "stdin": True,
                    "stdinOnce": True,
                    "tty": True,
                    "volumeMounts": [
                        {
                            "name": "home",
                            "mountPath": "/home",
                        }
                    ],
                    "securityContext": {"allowPrivilegeEscalation": False},
                }
            ],
        },
    }

    # Command that creates the pod described above
    create_pod_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "run",
        pod_name,
        "--overrides",
        json.dumps(pod),
        "--image",
        # Use ubuntu image so we get GNU cp and other tools
        # Should match what we have in our pod definition
        "ubuntu:jammy",
        pod_name,
    ]

    # Command that waits for the pod above to be ready
    wait_for_pod_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "wait",
        "pods",
        "-l",
        f"run={pod_name}",
        "--for",
        "condition=Ready",
        "--timeout=90s",
    ]

    # Command that lists the contents of the source and destination home dirs
    ls_dirs_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "exec",
        pod_name,
        "--",
        "ls",
        "-lath",
        f"/home/{source_user}",
        f"/home/{destination_user}",
    ]

    # Command that copies the home directory of the source user
    # into the home directory of the destination user
    # under a directory located at `/home/{destination_user}/{source_user}-homedir``
    copy_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "exec",
        pod_name,
        "--",
        "cp",
        # preserve all attributes of the directory being copied
        "--archive",
        # do not overwrite any existing files at the destination
        "--no-clobber",
        # copy directories recursively
        "--recursive",
        f"/home/{source_user}",
        f"/home/{destination_user}/{source_user}-homedir",
    ]

    # Command to delete the pod we created
    delete_pod_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "delete",
        "pod",
        pod_name,
    ]

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        try:
            print_colour(
                f"Creating a pod with the home directories of {cluster_name} - {hub_name} hub mounted on /home...",
                "yellow",
            )
            subprocess.check_call(create_pod_cmd)
            subprocess.check_call(wait_for_pod_cmd)

            print_colour(
                f"Attention! You are about to start transferring the home dir of {source_user} into the home dir of {destination_user}/{source_user}-homedir",
                "yellow",
            )
            confirm = typer.confirm("Are you sure you want to continue?")
            if not confirm:
                raise typer.Abort()

            print_colour("The content of the source and destination home dirs is:")
            subprocess.check_call(ls_dirs_cmd)

            print_colour("Starting the transfer...", "yellow")
            subprocess.check_call(copy_cmd)
            print_colour(
                "Done! The content of the source and destination home dirs now is:"
            )
            subprocess.check_call(ls_dirs_cmd)
        finally:
            print_colour("Deleting the pod...", "red")
            subprocess.check_call(delete_pod_cmd)


if __name__ == "__main__":
    app()
