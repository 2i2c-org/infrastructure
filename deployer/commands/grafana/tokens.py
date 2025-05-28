"""
This code is responsible for providing the deployer script's new-grafana-token
command meant to be run once as part of setting up a new cluster.

The new-grafana-token command makes use of a hardcoded admin password to create
a grafana service account named "deployer" and an access token for it. This
access token is written to a enc-grafana-token.secret.yaml file for use by the
deployer command going forward.
"""

import json
import os
import subprocess
from base64 import b64encode

import requests
import typer
from ruamel.yaml import YAML

from deployer.cli_app import grafana_app
from deployer.infra_components.cluster import Cluster
from deployer.utils.file_acquisition import (
    REPO_ROOT_PATH,
    get_decrypted_file,
)
from deployer.utils.rendering import print_colour

yaml = YAML(typ="safe")


def get_grafana_admin_password():
    """
    Retrieve the password of the grafana `admin` user
    stored in "helm-charts/support/enc-support.secret.values.yaml"

    Returns:
        string object: password of the admin user
    """
    grafana_credentials_filename = REPO_ROOT_PATH.joinpath(
        "helm-charts/support/enc-support.secret.values.yaml"
    )

    with get_decrypted_file(grafana_credentials_filename) as decrypted_path:
        with open(decrypted_path) as f:
            grafana_creds = yaml.load(f)

    return grafana_creds.get("grafana", {}).get("adminPassword", None)


def update_central_grafana_token(cluster_name, token):
    """
    Update the API token stored in the `enc-grafana-token.secret.yaml` file
    for the <cluster_name>'s Grafana.
    This access token should have enough permissions to create datasources.

    - If the file `enc-grafana-token.secret.yaml` doesn't exist, it creates one and
      writes the `token` under `grafana_token` key.
    - If the file `enc-grafana-token.secret.yaml` already exists, it updates the token in it by
      first deleting the file and then creating a new (encrypted) one
      where it writes the `token` under `grafana_token` key.
    """
    # Get the location of the file that stores the central grafana token
    cluster = Cluster.from_name(cluster_name)

    grafana_token_file = cluster.config_dir / "enc-grafana-token.secret.yaml"

    # If grafana token file exists delete it and then create it again with new token
    # Fastest way to update the token
    if os.path.exists(grafana_token_file):
        os.remove(grafana_token_file)

    with open(grafana_token_file, "w") as f:
        f.write(f"grafana_token: {token}")

    # Encrypt the private key
    subprocess.check_call(["sops", "--in-place", "--encrypt", grafana_token_file])


def build_service_account_request_headers():
    """
    Build the headers needed to send requests to the Grafana service account endpoint.

    Returns:
        dict: "Accept", "Content-Type", "Authorization" headers
    """
    # Get grafana credentials
    grafana_username = "admin"
    grafana_password = get_grafana_admin_password()
    credentials = f"{grafana_username}:{grafana_password}"
    basic_auth_credentials = b64encode(credentials.encode("utf-8"))

    # Build and return the headers
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic " + basic_auth_credentials.decode("utf-8"),
    }


def create_deployer_service_account(sa_endpoint, headers):
    """
    Create a Grafana service account with the name: `deployer`

    Returns:
        id: the id of the service account with the name `deployer`
    """

    request_body = {"name": "deployer", "role": "Admin", "isDisabled": False}

    # Create a service account called `deployer` in the cluster's grafana
    response = requests.post(
        sa_endpoint,
        data=json.dumps(request_body),
        headers=headers,
    )
    if not response.ok:
        print(
            "An error occurred while creating the service account for the deployer.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()
    print_colour("Successfully created the `deployer` sa!")

    return response.json()["id"]


def get_deployer_service_account_id(sa_endpoint, headers):
    """
    Iterate the list of service accounts registered for a Grafana host,
    identified by its service account endpoint (`sa_endpoint`), and
    retrieve the id of the service account which has the name "deployer".

    Assumes:
        the maximum number of service accounts created for a grafana is no more than 10.

    Returns:
        id: the id of the service account with the name `deployer` or
            `None` if no service account with this name was found
    """

    # Assumes we don't have more than 10 service accounts created for a Grafana
    # FIXME if this changes
    max_sa = 10
    sa_first_page_endpoint = f"{sa_endpoint}/search?perpage={max_sa}&page=1"
    response = requests.get(sa_first_page_endpoint, headers=headers)

    if not response.ok:
        print(
            f"An error occurred when retrieving the service accounts from {sa_first_page_endpoint}.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()

    service_account_no = response.json()["totalCount"]
    if service_account_no == 0:
        return

    service_accounts = response.json()["serviceAccounts"]
    return next((sa["id"] for sa in service_accounts if sa["name"] == "deployer"), None)


def get_deployer_token(sa_endpoint, sa_id, headers):
    """
    Iterate the list of tokens created for the `deployer` service account and
    retrieve the token with the name `deployer`.

    Returns:
        token, if deployer token exists
        None otherwise
    """
    response = requests.get(
        f"{sa_endpoint}/{sa_id}/tokens",
        headers=headers,
    )
    if not response.ok:
        print(
            f"An error occurred when retrieving the tokens the service account with id {sa_id}.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()

    for token in response.json():
        if token["name"] == "deployer":
            return token

    return


def create_deployer_token(sa_endpoint, sa_id, headers):
    token_request_body = {"name": "deployer", "role": "Admin"}
    response = requests.post(
        f"{sa_endpoint}/{sa_id}/tokens",
        data=json.dumps(token_request_body),
        headers=headers,
    )

    if not response.ok:
        print(
            "An error occurred when creating the token for the deployer service account.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()

    print_colour("Successfully generated the `deployer` token!")

    return response.json()["key"]


@grafana_app.command()
def new_token(
    cluster_name=typer.Argument(
        ...,
        help="Name of cluster for who's Grafana deployment to generate a new deployer token",
    )
):
    """
    Generate an API token for the cluster's Grafana `deployer` service account
    and store it encrypted inside a `enc-grafana-token.secret.yaml` file.
    """
    cluster = Cluster.from_name(cluster_name)
    grafana_url = cluster.get_grafana_url()
    sa_endpoint = f"{grafana_url}/api/serviceaccounts"
    headers = build_service_account_request_headers()

    overwrite = False
    token = None

    # Check if there's a service account called "deployer" already
    sa_id = get_deployer_service_account_id(sa_endpoint, headers)
    if not sa_id:
        print_colour("Creating a `deployer` service account...", "yellow")
        sa_id = create_deployer_service_account(sa_endpoint, headers)
    else:
        # Check if there's a "deployer" token for the "deployer service account" already
        token = get_deployer_token(sa_endpoint, sa_id, headers)

    if token:
        has_expired = token["hasExpired"]
        if has_expired:
            print_colour(
                "A token with the name `deployer` already exists but it has expired!",
                "red",
            )
        else:
            print_colour(
                "A token with the name `deployer` already exists!",
                "yellow",
            )
            print_colour(
                "Type `yes` if you want to overwrite it or anything else to abort...",
            )
            overwrite = input()
            if overwrite != "yes":
                print_colour("Aborting...", "red")
                return

        print_colour("Deleting the token...", "yellow")
        response = requests.delete(
            f'{sa_endpoint}/{sa_id}/tokens/{token["id"]}',
            headers=headers,
        )
        response.raise_for_status()

    # Create a token called `deployer` for the newly created `deployer` service account
    print_colour(
        "Generating a new token for the Grafana `deployer` service account...", "yellow"
    )
    token = create_deployer_token(sa_endpoint, sa_id, headers)

    update_central_grafana_token(cluster, token)
