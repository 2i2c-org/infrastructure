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
