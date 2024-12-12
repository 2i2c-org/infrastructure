import json
import os
import tempfile
import subprocess

import typer
from ruamel.yaml import YAML

from deployer.cli_app import exec_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import find_absolute_path_to_cluster_file
from deployer.utils.rendering import print_colour

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)
# Define the numerical version of the ubuntu image
# used by the helper pods created by this script
# in one central place to update it more easily
UBUNTU_IMAGE = "ubuntu:22.04"


@exec_app.command()
def root_homes(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    rm_pod: bool = typer.Option(False, "--rm", help="Automatically delete the pod after completing"),
    extra_nfs_server: str = typer.Option(
        None, help="IP address of an extra NFS server to mount"
    ),
    extra_nfs_base_path: str = typer.Option(
        None, help="Path of the extra NFS share to mount"
    ),
    extra_nfs_mount_path: str = typer.Option(
        None, help="Mount point for the extra NFS share"
    ),
):
    """
    Pop an interactive shell with the entire nfs file system of the given cluster mounted on /root-homes
    Optionally mount an extra NFS share if required (useful when migrating data to a new NFS server).
    """
    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)

    hubs = cluster.hubs
    hub = next((hub for hub in hubs if hub.spec["name"] == hub_name), None)
    if not hub:
        print_colour("Hub does not exist in {cluster_name} cluster}")
        return

    server_ip = base_share_name = ""
    for values_file in hub.spec["helm_chart_values_files"]:
        if "secret" not in os.path.basename(values_file):
            values_file = config_file_path.parent.joinpath(values_file)
            config = yaml.load(values_file)

            if config.get("basehub", {}):
                config = config["basehub"]

            server_ip = config.get("nfs", {}).get("pv", {}).get("serverIP", server_ip)
            base_share_name = (
                config.get("nfs", {})
                .get("pv", {})
                .get("baseShareName", base_share_name)
            )

    pod_name = f"{cluster_name}-root-home-shell"
    volumes = [
        {
            "name": "root-homes",
            "nfs": {"server": server_ip, "path": base_share_name},
        }
    ]
    volume_mounts = [
        {
            "name": "root-homes",
            "mountPath": "/root-homes",
        }
    ]

    if extra_nfs_server and extra_nfs_base_path and extra_nfs_mount_path:
        volumes.append(
            {
                "name": "extra-nfs",
                "nfs": {"server": extra_nfs_server, "path": extra_nfs_base_path},
            }
        )
        volume_mounts.append(
            {
                "name": "extra-nfs",
                "mountPath": extra_nfs_mount_path,
            }
        )

    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": hub_name,
        },
        "spec": {
            "terminationGracePeriodSeconds": 1,
            "automountServiceAccountToken": False,
            "volumes": volumes,
            "containers": [
                {
                    "name": pod_name,
                    # Use ubuntu image so we get better gnu rm
                    "image": UBUNTU_IMAGE,
                    "stdin": True,
                    "stdinOnce": True,
                    "tty": True,
                    "volumeMounts": volume_mounts,
                }
            ],
        },
    }

    # Ask kube-controller to create a pod
    create_cmd = ["kubectl", "create", "-f"]

    # Dump the pod spec to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmpf:
        json.dump(pod, tmpf)

    create_cmd.append(tmpf.name)

    # Command to exec into pod
    exec_cmd = [
        "kubectl", "-n", hub_name, "exec", "-it", pod_name, "--", "/bin/bash", "-l"
    ]

    with cluster.auth():
        subprocess.check_call(create_cmd)
        subprocess.check_call(exec_cmd)

        # I want to ensure this code runs event if the exec cmd returns an exit code other than 0
        if rm_pod:
            delete_pod(pod_name, hub_name)

    # I want to ensure this code runs event if the exec cmd returns an exit code other than 0
    # Delete temporary pod spec file
    os.remove(tmpf.name)


@exec_app.command()
def homes(
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
                    "image": UBUNTU_IMAGE,
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
        UBUNTU_IMAGE,
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


@exec_app.command()
def hub(
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


def create_ready_home_pod_jupyter_user(pod_name, cluster_name, hub_name):
    """
    Function that:
        - creates a pod with with the home directories of <cluster_name>-<hub_name> hub mounted on /home
        - starts a container for the jupyter user, uuid 1000 in this pod
        - waits for the pod  to be ready
    """
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
                    "image": UBUNTU_IMAGE,
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
        UBUNTU_IMAGE,
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

    print_colour(
        f"Creating a pod with the home directories of {cluster_name} - {hub_name} hub mounted on /home...",
        "yellow",
    )
    subprocess.check_call(create_pod_cmd)
    subprocess.check_call(wait_for_pod_cmd)


def ask_for_dirname_again():
    """
    Function that asks the user to provide the name of the source and dest directories using typer prompts.

    Returns the name of the source and dest directories as a tuple if they were provided by the user
    or the None, None tuple.
    """
    print_colour("Asking for the dirs again...", "yellow")
    continue_with_dir_names_confirmation = typer.confirm(
        "Can you now provide the names of the source and destination home directories?"
    )
    if not continue_with_dir_names_confirmation:
        return None, None

    source_homedir = typer.prompt(
        "What is the (escaped) name of source homedir that will be copied?"
    )
    destination_homedir = typer.prompt(
        "What is the (escaped) name of destination homedir where the files will be copied?"
    )

    return source_homedir, destination_homedir


def ls_home_dir(hub_name, pod_name):
    """
    List the contents of /home in <pod_name>
    """
    print_colour("Listing the content of the /home directory instead...", "yellow")
    # Command that lists the contents of /home directory
    ls_home_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "exec",
        pod_name,
        "--",
        "ls",
        "-lath",
        "/home",
    ]
    subprocess.check_call(ls_home_cmd)


def ls_source_and_dest_dirs(source_dir, dest_dir, hub_name, pod_name):
    """
    Lists the content of <source_dir> and <dest_dir> in <pod_name>
    """
    # Command that lists the contents of the source and destination home dirs
    ls_source_and_dest_dirs_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "exec",
        pod_name,
        "--",
        "ls",
        "-lath",
        f"/home/{source_dir}",
        f"/home/{dest_dir}",
    ]
    print_colour("The content of the source and destination home dirs is:")
    subprocess.check_call(ls_source_and_dest_dirs_cmd)


def copy_into_subdir(source_dir, dest_dir, hub_name, pod_name):
    """
    Copy the source home directory <source_dir>,
    into the home directory of the destination directory <dest_dir>,
    under a directory located at `/home/<dest_dir>/<source_dir>-homedir`
    """
    print_colour("Starting the copying process...", "yellow")
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
        f"/home/{source_dir}",
        f"/home/{dest_dir}/{source_dir}-homedir",
    ]
    subprocess.check_call(copy_cmd)
    print_colour("Done!")


def delete_pod(pod_name, hub_name):
    """
    Delete the <pod_name> from <hub_name> namespace
    """
    print_colour("Deleting the pod...", "red")
    # Command to delete the pod we created
    delete_pod_cmd = [
        "kubectl",
        "-n",
        hub_name,
        "delete",
        "pod",
        pod_name,
    ]
    subprocess.check_call(delete_pod_cmd)


@exec_app.command()
def copy_homedir_into_another(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(..., help="Name of hub to operate on"),
    source_homedir: str = typer.Option(
        None,
        help="Name of source homedir that we are transferring. "
        "This is usually the escaped username, eg. user-402i2c-2eorg."
        "If none is provided, the command will just list all of the homedirs available on the hub.",
    ),
    destination_homedir: str = typer.Option(
        None,
        help="Name of destination homedir where we will be copying over the files. "
        "This is usually the escaped username, eg. user-402i2c-2eorg. "
        "If none is provided, the command will just list all of the homedirs available on the hub.",
    ),
):
    """
    Start a pod with the home directories of the given hub mounted on /home and run a container as the jupyter user (uuid 1000) in this pod.
    Use this container to run commands to copy the source home directory <source_dir>, into the home directory of the destination directory <dest_dir>,
    under a directory located at `/home/<dest_dir>/<source_dir>-homedir`.
    Delete the pod when the copying is done or if any exception is raised.
    """
    # Name the pod so we know what to delete when the transfer is done
    pod_name = f"{cluster_name}-{hub_name}-transfer-shell"

    config_file_path = find_absolute_path_to_cluster_file(cluster_name)
    with open(config_file_path) as f:
        cluster = Cluster(yaml.load(f), config_file_path.parent)
    with cluster.auth():
        try:
            # Create the pod that mounts the /home directory and wait for it to be ready
            create_ready_home_pod_jupyter_user(pod_name, cluster_name, hub_name)

            # Check if a source and destination home directory names have been provided as cmd flags
            # If not, then ls the contents of /home and ask for them again
            if not source_homedir or not destination_homedir:
                print_colour(
                    "The names of the source and destination home directories were not provided. ",
                    "red",
                )
                ls_home_dir(hub_name, pod_name)
                source_homedir, destination_homedir = ask_for_dirname_again()
                if not source_homedir or not destination_homedir:
                    raise typer.Abort()

            print_colour(
                f"Attention! You are about to start copying the home dir of {source_homedir} into the home dir of {destination_homedir}/{source_homedir}-homedir",
                "yellow",
            )
            confirm = typer.confirm("Are you sure you want to continue?")
            if not confirm:
                raise typer.Abort()

            # First list the contents of the source and dest dirs
            ls_source_and_dest_dirs(
                source_homedir, destination_homedir, hub_name, pod_name
            )
            # Copy the actual data from /home/<source_homedir> to /home/<destination_homedir>/<source-homedir>-homedir
            copy_into_subdir(source_homedir, destination_homedir, hub_name, pod_name)
            # List the dirs again to double check everything happened as it should
            ls_source_and_dest_dirs(
                source_homedir, destination_homedir, hub_name, pod_name
            )
        finally:
            delete_pod(pod_name, hub_name)
