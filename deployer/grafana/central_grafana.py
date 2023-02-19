"""
Each cluster deployed should have a Grafana and Prometheus instance running via
the support chart, but the 2i2c cluster's Grafana instance is special, and we
refer it as the central Grafana instance at https://grafana.pilot.2i2c.cloud.

This code provides the deployer's update-central-grafana-datasources command,
that ensures that the central grafana instance is able to access datasources the
other clusters.
"""

import json

import requests
import typer
from ruamel.yaml import YAML

from ..cli_app import app
from ..helm_upgrade_decision import get_all_cluster_yaml_files
from ..utils import print_colour
from .grafana_utils import (
    get_cluster_prometheus_address,
    get_cluster_prometheus_creds,
    get_grafana_token,
    get_grafana_url,
)

yaml = YAML(typ="safe")


def build_datasource_details(cluster_name):
    """
    Build the payload needed to create an authenticated datasource in Grafana for `cluster_name`.

    Args:
        cluster_name: name of the cluster
    Returns:
        dict object: req payload to be consumed by Grafana
    """
    # Get the prometheus address for cluster_name
    datasource_url = get_cluster_prometheus_address(cluster_name)

    # Get the credentials of this prometheus instance
    prometheus_creds = get_cluster_prometheus_creds(cluster_name)

    datasource_details = {
        "name": cluster_name,
        "type": "prometheus",
        "access": "proxy",
        "url": f"https://{datasource_url}",
        "basicAuth": True,
        "basicAuthUser": prometheus_creds["username"],
        "secureJsonData": {"basicAuthPassword": prometheus_creds["password"]},
    }

    return datasource_details


def build_datasource_request_headers(cluster_name):
    """
    Build the headers needed to send requests to the Grafana datasource endpoint.

    Returns:
        dict: "Accept", "Content-Type", "Authorization" headers
    """
    token = get_grafana_token(cluster_name)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    return headers


def get_clusters_used_as_datasources(cluster_name, datasource_endpoint):
    """
    Get the list of cluster names that have prometheus instances
    already defined as datasources of the central Grafana.

    Returns:
        list: the name of the clusters registered as central Grafana datasources
    """
    headers = build_datasource_request_headers(cluster_name)

    # Get the list of all the currently existing datasources
    response = requests.get(datasource_endpoint, headers=headers)

    if not response.ok:
        print(
            f"An error occured when retrieving the datasources from {datasource_endpoint}.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()
    datasources = response.json()

    return [datasource["name"] for datasource in datasources]


@app.command()
def update_central_grafana_datasources(
    central_grafana_cluster=typer.Argument(
        "2i2c", help="Name of cluster where the central grafana lives"
    )
):
    """
    Update the central grafana with datasources for all clusters prometheus instances
    """
    grafana_url = get_grafana_url(central_grafana_cluster)
    datasource_endpoint = f"{grafana_url}/api/datasources"

    # Get a list of the clusters that already have their prometheus instances used as datasources
    datasources = get_clusters_used_as_datasources(
        central_grafana_cluster, datasource_endpoint
    )

    # Get a list of filepaths to all cluster.yaml files in the repo
    cluster_files = get_all_cluster_yaml_files()

    print("Searching for clusters that aren't Grafana datasources...")
    # Count how many clusters we can't add as datasources for logging
    exceptions = 0
    for cluster_file in cluster_files:
        # Read in the cluster.yaml file
        with open(cluster_file) as f:
            cluster_config = yaml.load(f)

        # Get the cluster's name
        cluster_name = cluster_config.get("name", {})
        if cluster_name and cluster_name not in datasources:
            print(f"Found {cluster_name} cluster. Checking if it can be added...")
            # Build the datasource details for the instances that aren't configures as datasources
            try:
                datasource_details = build_datasource_details(cluster_name)
                req_body = json.dumps(datasource_details)

                # Tell Grafana to create and register a datasource for this cluster
                headers = build_datasource_request_headers(central_grafana_cluster)
                response = requests.post(
                    datasource_endpoint, data=req_body, headers=headers
                )
                if not response.ok:
                    print(
                        f"An error occured when creating the datasource. \nError was {response.text}."
                    )
                    response.raise_for_status()
                print_colour(
                    f"Successfully created a new datasource for {cluster_name}!"
                )
            except Exception as e:
                print_colour(
                    f"An error occured for {cluster_name}.\nError was: {e}.\nSkipping...",
                    "yellow",
                )
                exceptions += 1
                pass

    if exceptions:
        print_colour(
            f"Failed to add {exceptions} clusters as datasources. See errors above!",
            "red",
        )
    print_colour(
        f"Successfully retrieved {len(datasources)} existing datasources! {datasources}"
    )
