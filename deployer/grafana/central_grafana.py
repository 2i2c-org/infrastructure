"""
### Summary

Ensures that the central grafana at https://grafana.pilot.2i2c.cloud is configured to use as datasource the authenticated prometheus instances of all the clusters that we run.

### How to use

This is meant to by run as a script from the command line, like so:

$ python deployer/grafana_datasources_manager.py

"""

import json
import subprocess
from base64 import b64encode
from pathlib import Path

import requests
import typer
from ruamel.yaml import YAML

from .cli_app import app
from .grafana_manager_utils import (
    get_central_grafana_token,
    get_cluster_prometheus_address,
    get_cluster_prometheus_creds,
    get_grafana_url,
    update_central_grafana_token,
)
from .helm_upgrade_decision import get_all_cluster_yaml_files
from .utils import print_colour

yaml = YAML(typ="safe")
REPO_ROOT = Path(__file__).parent.parent


def build_datasource_details(cluster_name):
    """Builds the payload needed to create an authenticated datasource in Grafana for `cluster_name`.

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
    token = get_central_grafana_token(cluster_name)

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    return headers


def get_clusters_used_as_datasources(cluster_name, datasource_endpoint):
    """Returns a list of cluster names that have prometheus instances already defined as datasources of the centralized Grafana."""
    headers = build_datasource_request_headers(cluster_name)
    # Get a list of all the currently existing datasources
    response = requests.get(datasource_endpoint, headers=headers)

    if response.status_code != 200:
        print(
            f"An error occured when retrieving the datasources from {datasource_endpoint}. \n Error was {response.text}."
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
    Update a central grafana with datasources for all our prometheuses
    """
    grafana_host = get_grafana_url(central_grafana_cluster)
    datasource_endpoint = f"https://{grafana_host}/api/datasources"

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
                if response.status_code != 200:
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


@app.command()
def generate_grafana_token_file(
    cluster=typer.Argument(..., help="Name of cluster where the central grafana lives")
):
    # Dencrypt grafana creds
    grafana_username = "admin"
    grafana_password_string = subprocess.check_output(
        [
            "sops",
            "--decrypt",
            REPO_ROOT / "helm-charts/support/enc-support.secret.values.yaml",
        ]
    ).decode("utf-8")

    # Find the admin username inside the sops output
    keyword = "adminPassword: "
    pass_idx = grafana_password_string.find(keyword) + len(keyword)
    grafana_password = grafana_password_string[pass_idx:-1]
    credentials = f"{grafana_username}:{grafana_password}"
    basic_auth_credentials = b64encode(credentials.encode("utf-8"))

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic " + basic_auth_credentials.decode("utf-8"),
    }

    request_body = {"name": "Deployer", "role": "Admin", "isDisabled": False}

    # Create a service account called "deployer in this cluster"
    grafana_host = get_grafana_url(cluster)
    print(request_body)
    response = requests.post(
        f"https://{grafana_host}/api/serviceaccounts",
        data=json.dumps(request_body),
        headers=headers,
    )
    if response.status_code != 201:
        print(
            f"An error occured when creating the service account for the deployer. \nError was {response.text}."
        )
        response.raise_for_status()
    print_colour(f"Successfully created a service account for the deployer!")

    sa_id = response.json()["id"]
    token_request_body = {"name": "deployer", "role": "Admin"}
    response = requests.post(
        f"https://{grafana_host}/api/serviceaccounts/{sa_id}/tokens",
        data=json.dumps(token_request_body),
        headers=headers,
    )

    if response.status_code != 201:
        print(
            f"An error occured when creating the token for the deployer service account. \nError was {response.text}."
        )
        response.raise_for_status()

    print_colour(f"Successfully generated a token for the deployer service account")
    token = response.json()["key"]

    update_central_grafana_token(cluster, token)
