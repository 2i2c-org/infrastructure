"""
Nested typer application nested under exec cost-monitoring sub-command of the deployer.
"""

import json
import subprocess

import typer

from deployer.cli_app import exec_app
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.dev_commands.exec.aws.aws_app import setup_aws_env
from deployer.infra_components.cluster import Cluster

cost_monitoring = typer.Typer(pretty_exceptions_show_locals=False)
exec_app.add_typer(
    cost_monitoring,
    name="cost-monitoring",
    help="Interact with a hub's jupyterhub-cost-monitoring service.",
)


def get_cost_monitoring_pod_name(namespace: str):
    """
    Return the pod name running the jupyterhub-cost-monitoring service.
    """
    pods = json.loads(
        subprocess.check_output(
            [
                "kubectl",
                "get",
                "pod",
                "-l",
                "app.kubernetes.io/name=jupyterhub-cost-monitoring",
                "-n",
                namespace,
                "-o",
                "json",
            ]
        ).decode()
    )
    if not pods.get("items"):
        raise ValueError(
            f"No pods with jupyterhub-cost-monitoring label running on {namespace} found."
        )
    assert len(pods["items"]) == 1

    pod = pods["items"][0]
    return pod["metadata"]["name"]


@cost_monitoring.command()
def list_active_tags(
    cluster_name: str = typer.Argument(help="Name of cluster/AWS profile."),
    mfa_device_id: str = typer.Argument(
        None,
        help="Full ARN of MFA Device the code is from (leave empty if not using MFA)",
    ),
    auth_token: str = typer.Argument(
        None,
        help="6 digit 2 factor authentication code from the MFA device (leave empty if not using MFA)",
    ),
):
    """
    Get a list of active cost allocation tags.
    """
    validate_cluster_config(cluster_name)
    cluster = Cluster.from_name(cluster_name)

    if cluster.spec["provider"] != "aws":
        raise ValueError(
            f"'{cluster_name}' is not on AWS, therefore the cost monitoring service is unavailable for this cluster at this time."
        )
    env = setup_aws_env(cluster_name, mfa_device_id, auth_token)
    try:
        subprocess.check_call(
            ["aws", "ce", "list-cost-allocation-tags", "--status=Active"], env=env
        )
    except subprocess.CalledProcessError as error:
        raise (error.output)
