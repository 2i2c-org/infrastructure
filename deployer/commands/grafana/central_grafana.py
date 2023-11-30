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

from deployer.cli_app import grafana_app
from deployer.utils.file_acquisition import get_all_cluster_yaml_files
from deployer.utils.rendering import print_colour

from .utils import (
    get_cluster_prometheus_address,
    get_cluster_prometheus_creds,
    get_grafana_token,
    get_grafana_url,
)

yaml = YAML(typ="safe")


def central_grafana_datasource_endpoint(central_grafana_cluster_name="2i2c"):
    grafana_url = get_grafana_url(central_grafana_cluster_name)
    return f"{grafana_url}/api/datasources"


def build_datasource_details(cluster_name, datasource_name=None):
    """
    Build the payload needed to create an authenticated datasource in Grafana for `cluster_name`.

    Args:
        cluster_name: name of the cluster who's prometheus instance will map to this datasource_name
        datasource_name: name of the datasource
    Returns:
        dict object: req payload to be consumed by Grafana
    """
    # Get the prometheus address for cluster_name
    datasource_url = get_cluster_prometheus_address(cluster_name)

    # Get the credentials of this prometheus instance
    prometheus_creds = get_cluster_prometheus_creds(cluster_name)

    datasource_name = cluster_name if not datasource_name else datasource_name
    datasource_details = {
        "name": datasource_name,
        "type": "prometheus",
        "access": "proxy",
        "url": f"https://{datasource_url}",
        "basicAuth": True,
        "basicAuthUser": prometheus_creds["username"],
        "secureJsonData": {"basicAuthPassword": prometheus_creds["password"]},
    }

    return datasource_details


def build_datasource_request_headers(central_grafana_cluster_name="2i2c"):
    """
    Build the headers needed to send requests to the Grafana datasource endpoint.

    Returns:
        dict: "Accept", "Content-Type", "Authorization" headers
    """
    token = get_grafana_token(central_grafana_cluster_name)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    return headers


def get_clusters_used_as_datasources(central_grafana_cluster_name="2i2c"):
    """
    Get the list of cluster names that have prometheus instances
    already defined as datasources of the central Grafana.

    Returns:
        list: the name of the clusters registered as central Grafana datasources
    """
    datasource_endpoint = central_grafana_datasource_endpoint(
        central_grafana_cluster_name
    )

    headers = build_datasource_request_headers()

    # Get the list of all the currently existing datasources
    response = requests.get(datasource_endpoint, headers=headers)

    if not response.ok:
        print(
            f"An error occurred when retrieving the datasources from {datasource_endpoint}.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()
    datasources = response.json()

    return [datasource["name"] for datasource in datasources]


@grafana_app.command()
def get_datasources_removal_candidates():
    """
    Get the datasources names that are registered in central grafana
    but are NOT in the list of clusters in the infrastructure repository.
    You might consider removing these datasources one by one, as they might link to
    decommissioned clusters.
    """
    # Get a list of the clusters that already have their prometheus instances used as datasources
    datasources = get_clusters_used_as_datasources()

    # Get the list of the names of clusters in the infrastructure repository
    cluster_files = get_all_cluster_yaml_files()
    cluster_names = [cluster.parents[0].name for cluster in cluster_files]

    rm_candidates = set(datasources).difference(cluster_names)

    if not rm_candidates:
        print_colour("Everything is up to date! :)")
        return

    print(
        "These datasources don't map to an existing cluster. You might consider removing them."
    )
    print_colour(f"{rm_candidates}", "yellow")


@grafana_app.command()
def get_datasources_add_candidates():
    """
    Get the clusters in the infrastructure repository but are NOT
    registered in central grafana as datasources.
    You might consider adding these datasources, as they might link to
    new clusters that haven't been updated.
    """

    # Get a list of the clusters that already have their prometheus instances used as datasources
    datasources = get_clusters_used_as_datasources()

    # Get the list of the names of clusters in the infrastructure repository
    cluster_files = get_all_cluster_yaml_files()
    cluster_names = [cluster.parents[0].name for cluster in cluster_files]

    add_candidates = set(cluster_names).difference(datasources)
    if not add_candidates:
        print_colour("Everything is up to date! :)")
        return

    print(
        "These datasources don't map to an existing cluster. You might consider removing them."
    )
    print_colour(f"{add_candidates}", "yellow")


@grafana_app.command()
def add_cluster_as_datasource(
    cluster_name=typer.Argument(
        ..., help="Name of cluster to add as a datasource to the central 2i2c grafana."
    ),
    datasource_name=typer.Option(
        "",
        help="(Optional) The name of the datasource to add. Defaults to cluster_name.",
    ),
):
    """
    Add a new cluster to the central 2i2c grafana.
    """
    datasource_name = cluster_name if not datasource_name else datasource_name
    datasource_endpoint = central_grafana_datasource_endpoint("2i2c")

    # Get a list of the clusters that already have their prometheus instances used as datasources
    datasources = get_clusters_used_as_datasources()
    if cluster_name and cluster_name not in datasources:
        print(f"Checking if {cluster_name} it can be added as datasource...")
        datasource_details = build_datasource_details(cluster_name)
        req_body = json.dumps(datasource_details)

        # Tell Grafana to create and register a datasource for this cluster
        headers = build_datasource_request_headers()
        response = requests.post(datasource_endpoint, data=req_body, headers=headers)
        if not response.ok:
            print_colour(f"{response.reason}.{response.json()['message']}.", "red")
            return

        print_colour(f"Successfully created a new datasource for {cluster_name}!")


@grafana_app.command()
def rm_entry_from_datasources(
    cluster_name=typer.Argument(
        ...,
        help="The name of cluster who's prometheus instance we're removing from the datasources in the central 2i2c grafana.",
    ),
    datasource_name=typer.Option(
        "",
        help="The name of the datasource we're removing. This is usually the same with the name of cluster.",
    ),
):
    """
    Update the central grafana with datasources for all clusters prometheus instances
    """
    datasource_name = cluster_name if not datasource_name else datasource_name
    datasource_endpoint = central_grafana_datasource_endpoint("2i2c")
    datasource_delete_endpoint = f"{datasource_endpoint}/name/{datasource_name}"

    # Get a list of the clusters that already have their prometheus instances used as datasources
    datasources = get_clusters_used_as_datasources()

    if datasource_name in datasources:
        print(f"Checking if {datasource_name} it can be deleted from datasources...")
        # Build the datasource details for the instances that aren't configures as datasources
        datasource_details = build_datasource_details(cluster_name, datasource_name)
        req_body = json.dumps(datasource_details)

        # Tell Grafana to create and register a datasource for this cluster
        headers = build_datasource_request_headers()
        response = requests.delete(
            datasource_delete_endpoint, data=req_body, headers=headers
        )
        if not response.ok:
            print_colour(f"{response.reason}. {response.json()['message']}.", "red")
            return

        print_colour(f"Successfully deleted the datasource of {datasource_name}!")
