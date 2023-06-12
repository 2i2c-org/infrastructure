"""
### Summary

Create/update/get/delete CILogon clients using the 2i2c administrative client provided by CILogon.
More details here: https://cilogon.github.io/oa4mp/server/manuals/dynamic-client-registration.html

### Use cases

The commands in this file can be used to:

- `create` a CILogon client application for a hub and store the credentials safely
- `update` the callback urls of an existing hub CILogon client
- `delete` a CILogon client application when a hub is removed or changes auth methods
- `get` details about an existing hub CILogon client
- `get-all` existing 2i2c CILogon client applications
"""

import base64
import json
from pathlib import Path

import requests
import typer
from ruamel.yaml import YAML
from yarl import URL

from .cli_app import app
from .file_acquisition import (
    build_absolute_path_to_hub_encrypted_config_file,
    get_decrypted_file,
    persist_config_in_encrypted_file,
    remove_jupyterhub_hub_config_key_from_encrypted_file,
)
from .utils import print_colour

yaml = YAML(typ="safe")


def build_request_headers(admin_id, admin_secret):
    token_string = f"{admin_id}:{admin_secret}"
    bearer_token = base64.urlsafe_b64encode(token_string.encode("utf-8")).decode(
        "ascii"
    )

    return {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def build_request_url(id=None):
    url = "https://cilogon.org/oauth2/oidc-cm"

    if id is None:
        return url

    return str(URL(url).with_query({"client_id": id}))


def build_client_details(cluster_name, hub_name, callback_url):
    return {
        "client_name": f"{cluster_name}-{hub_name}",
        "app_type": "web",
        "redirect_uris": [callback_url],
        "scope": "openid email org.cilogon.userinfo profile",
    }


def persist_client_credentials_in_config_file(client, hub_type, config_filename):
    auth_config = {}
    jupyterhub_config = {
        "jupyterhub": {
            "hub": {
                "config": {
                    "CILogonOAuthenticator": {
                        "client_id": client["client_id"],
                        "client_secret": client["client_secret"],
                    }
                }
            }
        }
    }

    if hub_type == "daskhub":
        auth_config["basehub"] = jupyterhub_config
    elif hub_type == "binderhub":
        auth_config["binderhub"] = jupyterhub_config
    else:
        auth_config = jupyterhub_config

    persist_config_in_encrypted_file(config_filename, auth_config)
    print_colour(
        f"Successfully persisted the encrypted CILogon client app credentials to file {config_filename}"
    )


def load_client_id_from_file(config_filename):
    with get_decrypted_file(config_filename) as decrypted_path:
        with open(decrypted_path) as f:
            auth_config = yaml.load(f)

    daskhub = auth_config.get("basehub", None)
    binderhub = auth_config.get("binderhub", None)
    try:
        if daskhub:
            return auth_config["basehub"]["jupyterhub"]["hub"]["config"][
                "CILogonOAuthenticator"
            ]["client_id"]
        elif binderhub:
            return auth_config["binderhub"]["jupyterhub"]["hub"]["config"][
                "CILogonOAuthenticator"
            ]["client_id"]
        return auth_config["jupyterhub"]["hub"]["config"]["CILogonOAuthenticator"][
            "client_id"
        ]
    except KeyError:
        return


def stored_client_id_same_with_cilogon_records(
    admin_id, admin_secret, cluster_name, hub_name, stored_client_id
):
    cilogon_client = get_client(admin_id, admin_secret, cluster_name, hub_name)
    if not cilogon_client:
        return False

    cilogon_client_id = cilogon_client.get("client_id", None)
    if cilogon_client_id != stored_client_id:
        return False

    return True


def print_not_ok_request_message(response):
    print_colour(
        f"The request to CILogon API returned a {response.status_code} status code.",
        "red",
    )
    print_colour(f"{response.text}", "yellow")


def create_client(
    admin_id, admin_secret, cluster_name, hub_name, hub_type, callback_url
):
    """Creates a new client

    Args:
        body (dict): Attributes for the new client

    Returns a dict containing the client details
    or None if the `create` request returned a status code not in the range 200-299.

    See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-post.sh
    """
    client_details = build_client_details(cluster_name, hub_name, callback_url)
    config_filename = build_absolute_path_to_hub_encrypted_config_file(
        cluster_name, hub_name
    )

    # Check if there's a client id already stored in the config file for this hub
    if Path(config_filename).is_file():
        client_id = load_client_id_from_file(config_filename)
        if client_id:
            print_colour(
                f"Found existing CILogon client app in {config_filename}.", "yellow"
            )
            # Also check if what's in the file matches CILogon records in case the file was not updated accordingly
            # Exit anyway since manual intervention is required if different
            if not stored_client_id_same_with_cilogon_records(
                admin_id, admin_secret, cluster_name, hub_name, client_id
            ):
                print_colour(
                    "CILogon records are different than the client app stored in the configuration file. Consider updating the file.",
                    "red",
                )
            return

    # Ask CILogon to create the client
    print(f"Creating a new CILogon client app with details {client_details}...")
    headers = build_request_headers(admin_id, admin_secret)
    response = requests.post(
        build_request_url(), json=client_details, headers=headers, timeout=5
    )

    if not response.ok:
        print_not_ok_request_message(response)
        return

    client = response.json()
    print_colour("Done! Successfully created a new CILogon client app.")

    # Persist and encrypt the client credentials
    return persist_client_credentials_in_config_file(client, hub_type, config_filename)


def update_client(admin_id, admin_secret, cluster_name, hub_name, callback_url):
    """Modifies a client by its id.

    ! The `client_secret` attribute cannot be updated.

    Note that any missing attribute values will be deleted from the client's stored information!
    Args:
        id (str): Id of the client to modify
        body (dict): Attributes to modify.

    Returns status code if response.ok
    or None if the `update` request returned a status code not in the range 200-299.

    See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-put.sh
    """
    client_details = build_client_details(cluster_name, hub_name, callback_url)
    config_filename = build_absolute_path_to_hub_encrypted_config_file(
        cluster_name, hub_name
    )
    if not Path(config_filename).is_file():
        print_colour("Can't update a client that doesn't exist", "red")
        return

    client_id = load_client_id_from_file(config_filename)
    if not client_id:
        print_colour("Can't update a client that doesn't exist", "red")
        return

    headers = build_request_headers(admin_id, admin_secret)
    response = requests.put(
        build_request_url(client_id), json=client_details, headers=headers, timeout=5
    )

    if not response.ok:
        print_not_ok_request_message(response)
        return

    print_colour("Done! Client updated successfully")


def get_client(admin_id, admin_secret, cluster_name, hub_name, client_id=None):
    """Retrieves a client by its id.

    Args:
        id (str): Id of the client to get

    Returns a dict containing the client details
    or None if the `get` request returned a status code not in the range 200-299.

    See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-get.sh
    """
    config_filename = build_absolute_path_to_hub_encrypted_config_file(
        cluster_name, hub_name
    )
    if not Path(config_filename).is_file():
        return

    if client_id:
        if not stored_client_id_same_with_cilogon_records(
            admin_id, admin_secret, cluster_name, hub_name, client_id
        ):
            print_colour(
                "CILogon records are different than the client app stored in the configuration file. Consider updating the file.",
                "red",
            )
            return

    client_id = load_client_id_from_file(config_filename)
    # No client has been found
    if not client_id:
        return

    headers = build_request_headers(admin_id, admin_secret)
    response = requests.get(
        build_request_url(client_id), params=None, headers=headers, timeout=5
    )

    if not response.ok:
        print_not_ok_request_message(response)
        return

    client_details = response.json()
    print(json.dumps(client_details, sort_keys=True, indent=4))
    return client_details


def delete_client(admin_id, admin_secret, cluster_name, hub_name, client_id=None):
    """Deletes the client associated with the id.

    Args:
        id (str): Id of the client to delete

    Returns status code if response.ok
    or None if the `delete` request returned a status code not in the range 200-299.

    See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-delete.sh
    """
    config_filename = build_absolute_path_to_hub_encrypted_config_file(
        cluster_name, hub_name
    )

    if not client_id:
        if Path(config_filename).is_file():
            client_id = load_client_id_from_file(config_filename)
            # Nothing to do if no client has been found
            if not client_id:
                print_colour(
                    "No `client_id` to delete was provided and couldn't find any in `config_filename`",
                    "red",
                )
                return
        else:
            print_colour(
                f"No `client_id` to delete was provided and couldn't find any {config_filename} file",
                "red",
            )
            return
    else:
        if not stored_client_id_same_with_cilogon_records(
            admin_id,
            admin_secret,
            cluster_name,
            hub_name,
            client_id,
        ):
            print_colour(
                "CILogon records are different than the client app stored in the configuration file. Consider updating the file.",
                "red",
            )
            return

    print(f"Deleting the CILogon client details for {client_id}...")
    headers = build_request_headers(admin_id, admin_secret)
    response = requests.delete(build_request_url(client_id), headers=headers, timeout=5)
    if not response.ok:
        print_not_ok_request_message(response)
        return

    print_colour("Done!")

    # Delete client credentials from config file also if file exists
    if Path(config_filename).is_file():
        print(f"Deleting the CILogon client details from the {config_filename} also...")
        key = "CILogonOAuthenticator"
        try:
            remove_jupyterhub_hub_config_key_from_encrypted_file(config_filename, key)
        except KeyError:
            print_colour(f"No {key} found to delete from {config_filename}", "yellow")
            return
        print_colour(f"CILogonAuthenticator config removed from {config_filename}")
        if not Path(config_filename).is_file():
            print_colour(f"Empty {config_filename} file also deleted.", "yellow")


def get_all_clients(admin_id, admin_secret):
    print("Getting all existing CILogon client applications...")
    headers = build_request_headers(admin_id, admin_secret)
    response = requests.get(
        build_request_url(), params=None, headers=headers, timeout=5
    )

    if not response.ok:
        print_not_ok_request_message(response)
        return

    clients = response.json()
    for c in clients["clients"]:
        print(c)


def get_2i2c_cilogon_admin_credentials():
    """
    Retrieve the 2i2c administrative client credentials
    stored in `shared/deployer/enc-auth-providers-credentials.secret.yaml`.
    """
    # This filepath is relative to the PROJECT ROOT
    general_auth_config = "shared/deployer/enc-auth-providers-credentials.secret.yaml"
    with get_decrypted_file(general_auth_config) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    return (
        config["cilogon_admin"]["client_id"],
        config["cilogon_admin"]["client_secret"],
    )


@app.command()
def cilogon_client_create(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        ..., help="Name of the hub for which we'll create a CILogon client"
    ),
    hub_type: str = typer.Argument(
        "basehub",
        help="Type of hub for which we'll create a CILogon client (ex: basehub, daskhub)",
    ),
    hub_domain: str = typer.Argument(
        ...,
        help="The hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud)",
    ),
):
    """Create a CILogon client for a hub."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    callback_url = f"https://{hub_domain}/hub/oauth_callback"
    create_client(
        admin_id, admin_secret, cluster_name, hub_name, hub_type, callback_url
    )


@app.command()
def cilogon_client_update(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        ..., help="Name of the hub for which we'll update a CILogon client"
    ),
    hub_domain: str = typer.Argument(
        ...,
        help="The hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud)",
    ),
):
    """Update the CILogon client of a hub."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    callback_url = f"https://{hub_domain}/hub/oauth_callback"
    update_client(admin_id, admin_secret, cluster_name, hub_name, callback_url)


@app.command()
def cilogon_client_get(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        ..., help="Name of the hub for which we'll retrieve the CILogon client details"
    ),
):
    """Retrieve details about an existing CILogon client."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    get_client(admin_id, admin_secret, cluster_name, hub_name)


@app.command()
def cilogon_client_get_all():
    """Retrieve details about all existing 2i2c CILogon clients."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    get_all_clients(admin_id, admin_secret)


@app.command()
def cilogon_client_delete(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate"),
    hub_name: str = typer.Argument(
        ...,
        help="Name of the hub for which we'll delete the CILogon client details",
    ),
    client_id: str = typer.Option(
        "",
        help="""(Optional) Id of the CILogon client to delete of the form `cilogon:/client_id/<id>`.
        If the id is not passed, it will be retrieved from the configuration file
        """,
    ),
):
    """Delete an existing CILogon client. This deletes both the CILogon client application,
    and the client credentials from the configuration file."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    delete_client(admin_id, admin_secret, cluster_name, hub_name, client_id)
