"""
Nested typer application nested under exec cost-monitoring sub-command of the deployer.
"""

import json
import subprocess

import requests
import typer
from yarl import URL

from deployer.cli_app import exec_app
from deployer.commands.validate.config import cluster_config as validate_cluster_config
from deployer.dev_commands.exec.aws.aws_app import setup_aws_sts_env
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
def query(cluster_name: str, subpath: str, verbose: bool = True):
    """
    Query jupyterhub-cost-monitoring-service for cost data.
    """
    cluster = Cluster.from_name(cluster_name)
    grafana_token = cluster.get_grafana_token()
    grafana_url = URL(cluster.get_grafana_url())
    api_url = grafana_url.with_path("api/datasources")
    datasource = requests.get(
        api_url.human_repr(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {grafana_token}",
        },
    )

    # Get the cost-monitoring yesoreyeram-infinity-datasource UID
    datasource_uid = datasource.json()[1]["uid"]
    target_url = URL("http://jupyterhub-cost-monitoring.support.svc.cluster.local")
    # See https://jupyterhub-cost-monitoring.readthedocs.io/en/latest/api/ for available endpoints
    subpath = "total-costs"

    headers = {
        "Authorization": f"Bearer {grafana_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "queries": [
            {
                "datasource": {
                    "type": "yesoreyeram-infinity-datasource",
                    "uid": datasource_uid,
                },
                "url": str(target_url / subpath),
                "url_options": {
                    "method": "GET",
                    "data": "",
                },
                "type": "json",
                "source": "url",
                "format": "table",
                "parser": "backend",
                "root_selector": "",
                # Columns can change depending on data returned by endpoint – see https://github.com/2i2c-org/jupyterhub-cost-monitoring/blob/a6e49c719e8600fc2490e2fb2a77da09ce4bcd1a/dashboards/common.libsonnet#L128 for examples from existing cloud cost grafana dashboards
                "columns": [
                    {"selector": "date", "text": "Date", "type": "timestamp"},
                    {"selector": "name", "text": "Name", "type": "string"},
                    {"selector": "cost", "text": "Cost", "type": "number"},
                ],
            }
        ],
        "from": "now-1d",
        "to": "now",
    }

    # https://grafana.com/docs/grafana-cloud/developer-resources/api-reference/http-api/data_source/#query-a-data-source
    query_url = grafana_url.with_path("api/ds/query")

    response = requests.post(
        query_url.human_repr(), headers=headers, data=json.dumps(payload)
    )

    if verbose:
        print(response.content.decode())

    return response


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
    env = setup_aws_sts_env(cluster_name, mfa_device_id, auth_token)
    subprocess.run(
        ["aws", "ce", "list-cost-allocation-tags", "--status=Active"], env=env
    )
