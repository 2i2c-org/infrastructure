import json
import subprocess
from base64 import b64encode
from pathlib import Path

import requests
import typer

from ..cli_app import app
from ..utils import print_colour
from .grafana_utils import get_grafana_url, update_central_grafana_token

REPO_ROOT = Path(__file__).parent.parent.parent


def build_service_account_request_headers():
    # Dencrypt grafana credentials file
    grafana_username = "admin"
    grafana_password_string = subprocess.check_output(
        [
            "sops",
            "--decrypt",
            REPO_ROOT / "helm-charts/support/enc-support.secret.values.yaml",
        ]
    ).decode("utf-8")

    # Parse the sops output to find the admin's username password
    keyword = "adminPassword: "
    pass_idx = grafana_password_string.find(keyword) + len(keyword)
    grafana_password = grafana_password_string[pass_idx:-1]
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
    Creates a Grafana service account with `deployer` name
    Returns:
        the service account's id
    """

    request_body = {"name": "deployer", "role": "Admin", "isDisabled": False}

    # Create a service account called `deployer` in the cluster's grafana
    response = requests.post(
        sa_endpoint,
        data=json.dumps(request_body),
        headers=headers,
    )
    if response.status_code != 200:
        print(
            f"An error occured when creating the service account for the deployer. \nError was {response.text}."
        )
        response.raise_for_status()
    print_colour("Successfully created a service account for the deployer!")

    return response.json()["id"]


def get_deployer_service_account_id(sa_endpoint, headers):
    # Assumes we don't have more than 10 service accounts created for a grafana
    # FIXME if this changes
    max_sa = 10
    sa_first_page_endpoint = f"{sa_endpoint}/search?perpage={max_sa}&page=1"
    response = requests.get(sa_first_page_endpoint, headers=headers)

    if response.status_code != 200:
        print(
            f"An error occured when retrieving the service accounts from {sa_first_page_endpoint}. \n Error was {response.text}."
        )
        response.raise_for_status()

    service_account_no = response.json()["totalCount"]
    if service_account_no == 0:
        return

    service_accounts = response.json()["serviceAccounts"]
    return next(sa["id"] for sa in service_accounts if sa["name"] == "deployer")


def get_deployer_token(sa_endpoint, sa_id, headers):
    """
    Returns:
        token, if deployer token exists
        False otherwise
    """
    response = requests.get(
        f"{sa_endpoint}/{sa_id}/tokens",
        headers=headers,
    )
    if response.status_code != 200:
        print(
            f"An error occured when retrieving the tokens the service account with id {sa_id}.\n"
            f"Error was {response.text}."
        )
        response.raise_for_status()

    for token in response.json():
        if token["name"] == "deployer":
            return token
    return False


@app.command()
def generate_grafana_token(
    cluster=typer.Argument(..., help="Name of cluster where the central grafana lives")
):
    grafana_host = get_grafana_url(cluster)
    sa_endpoint = f"https://{grafana_host}/api/serviceaccounts"
    headers = build_service_account_request_headers()

    sa_id = get_deployer_service_account_id(sa_endpoint, headers)

    if not sa_id:
        sa_id = create_deployer_service_account(sa_endpoint, headers)

    # Check if there's a "deployer" token already
    token = get_deployer_token(sa_endpoint, sa_id, headers)
    overwrite = False
    if token:
        print_colour(
            "Token already exists!\n"
            f'Checking if has expired: {token["hasExpired"]}\n',
            "yellow",
        )
        print_colour(
            "Type `yes` if you want to overwrite or anything else to abort...",
        )
        overwrite = input()

        if overwrite != "yes":
            print_colour("Aborting...", "red")
            return

    # Create a token called `deployer` for the newly created `deployer` service account
    print_colour(
        "Regenerating a token for the Grafana `deployer` service account", "yellow"
    )
    token_request_body = {"name": "deployer", "role": "Admin"}
    response = requests.post(
        f"https://{grafana_host}/api/serviceaccounts/{sa_id}/tokens",
        data=json.dumps(token_request_body),
        headers=headers,
    )

    if response.status_code != 200:
        print(
            f"An error occured when creating the token for the deployer service account. \nError was {response.text}."
        )
        response.raise_for_status()

    print_colour("Successfully generated a token for the deployer service account")
    token = response.json()["key"]

    update_central_grafana_token(cluster, token)
