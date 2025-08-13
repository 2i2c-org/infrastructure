"""
Actions available provisioning credentials to deploy against Kubernetes clusters
"""

import os
import subprocess

import typer
from ruamel.yaml import YAML

from deployer.cli_app import app
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.infra_components.cluster import Cluster

# Without `pure=True`, I get an exception about str / byte issues
yaml = YAML(typ="safe", pure=True)


@app.command()
def use_cluster_credentials(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    commandline: str = typer.Argument(
        "",
        help="Optional shell command line to run after authenticating to this cluster",
    ),
):
    """
    Pop a new shell or execute a command after authenticating to the given cluster using the deployer's credentials
    """
    if "DEPLOYER_NO_NESTED_KUBECONFIG" in os.environ and "KUBECONFIG" in os.environ:
        raise RuntimeError(
            "Attempting to create a nested KUBECONFIG context, which has been explicitly forbidden by the presence of the DEPLOYER_NO_NESTED_KUBECONFIG environment variable."
        )
    # This function is to be used with the `use-cluster-credentials` CLI
    # command only - it is not used by the rest of the deployer codebase.
    validate_cluster_config(cluster_name)

    cluster = Cluster.from_name(cluster_name)

    # Cluster.auth() method has the context manager decorator so cannot call
    # it like a normal function
    with cluster.auth():
        # This command will spawn a new shell with all the env vars (including
        # KUBECONFIG) inherited, and once you quit that shell the python program
        # will resume as usual.
        # TODO: Figure out how to change the PS1 env var of the spawned shell
        # to change the prompt to f"cluster-{cluster.spec['name']}". This will
        # make it visually clear that the user is now operating in a different
        # shell.
        args = [os.environ["SHELL"], "-l"]
        # If a command to execute is specified, just execute that and exit.
        if commandline:
            args += ["-c", commandline]
        subprocess.check_call(args)
