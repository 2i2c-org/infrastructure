"""
This code is responsible for providing the deployer script's new-grafana-token
command meant to be run once as part of setting up a new cluster.

The new-grafana-token command makes use of a hardcoded admin password to create
a grafana service account named "deployer" and an access token for it. This
access token is written to a enc-grafana-token.secret.yaml file for use by the
deployer command going forward.
"""

import json
from base64 import b64encode
from pathlib import Path

import requests
import typer

from ..cli_app import app
from ..utils import print_colour
from .grafana_utils import (
    get_grafana_admin_password,
    get_grafana_url,
    update_central_grafana_token,
)

REPO_ROOT = Path(__file__).parent.parent.parent


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
            f"An error occured when retrieving the tokens the service account with id {sa_id}.\n"
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
            "An error occured when creating the token for the deployer service account.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()

    print_colour("Successfully generated the `deployer` token!")

    return response.json()["key"]


@app.command()
def new_grafana_token(
    cluster=typer.Argument(
        ...,
        help="Name of cluster for who's Grafana deployment to generate a new deployer token",
    )
):
    """
    Generate an API token for the cluster's Grafana `deployer` service account
    and store it encrypted inside a `enc-grafana-token.secret.yaml` file.
    """
    grafana_url = get_grafana_url(cluster)
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
