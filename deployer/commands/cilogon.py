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
- `cleanup` duplicated CILogon applications
"""

import base64
import json
from collections import Counter
from pathlib import Path

import requests
import typer
from ruamel.yaml import YAML
from yarl import URL

from deployer.cli_app import cilogon_client_app
from deployer.utils.file_acquisition import (
    build_absolute_path_to_hub_encrypted_config_file,
    find_absolute_path_to_cluster_file,
    get_cluster_names_list,
    get_decrypted_file,
    persist_config_in_encrypted_file,
    remove_jupyterhub_hub_config_key_from_encrypted_file,
)
from deployer.utils.rendering import print_colour

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


def persist_client_credentials_in_config_file(client, config_filename):
    auth_config = {
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

    persist_config_in_encrypted_file(config_filename, auth_config)
    print_colour(
        f"Successfully persisted the encrypted CILogon client app credentials to file {config_filename}"
    )


def load_client_id_from_file(config_filename):
    with get_decrypted_file(config_filename) as decrypted_path:
        with open(decrypted_path) as f:
            auth_config = yaml.load(f)

    daskhub_legacy_config = auth_config.get("basehub", None)
    try:
        if daskhub_legacy_config:
            return auth_config["basehub"]["jupyterhub"]["hub"]["config"][
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


def create_client(admin_id, admin_secret, cluster_name, hub_name, callback_url):
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
    return persist_client_credentials_in_config_file(client, config_filename)


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


def delete_client(admin_id, admin_secret, client_id=None):
    """Deletes a CILogon client.

    Returns status code if response.ok
    or None if the `delete` request returned a status code not in the range 200-299.

    See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-delete.sh
    """
    if client_id is None:
        print("Deleting a CILogon client for unknown ID")
    else:
        print(f"Deleting the CILogon client details for {client_id}...")

    headers = build_request_headers(admin_id, admin_secret)
    response = requests.delete(build_request_url(client_id), headers=headers, timeout=5)
    if not response.ok:
        print_not_ok_request_message(response)
        return

    print_colour("Done!")


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
    return [c for c in clients["clients"]]


def find_duplicated_clients(clients):
    """Determine duplicated CILogon clients by comparing client names

    Args:
        clients (list[dict]): A list of dictionaries containing information about
            the existing CILogon clients. Generated by get_all_clients function.

    Returns:
        list: A list of duplicated client names
    """
    client_names = [c["name"] for c in clients]
    client_names_count = Counter(client_names)
    return [
        print(
            f"Found a duplicated entry for {k}. Marking the unused client for deletion."
        )
        or k
        for k, v in client_names_count.items()
        if v > 1
    ]


def find_orphaned_clients(clients):
    """Find CILogon clients for which an associated cluster or hub no longer
    exists and can safely be deleted.

    Args:
        clients (list[dict]): A list of existing CILogon client info

    Returns:
        list[dict]: A list of 'orphaned' CILogon clients which don't have an
            associated cluster or hub, which can be deleted
    """
    clients_to_be_deleted = []
    clusters = get_cluster_names_list()

    for client in clients:
        cluster = next((cl for cl in clusters if cl in client["name"]), "")

        if cluster:
            cluster_config_file = find_absolute_path_to_cluster_file(cluster)
            with open(cluster_config_file) as f:
                cluster_config = yaml.load(f)

            hub = next(
                (
                    hub["name"]
                    for hub in cluster_config["hubs"]
                    if hub["name"] in client["name"]
                ),
                "",
            )

            if not hub:
                print(
                    f"A hub pertaining to client {client['name']} does NOT exist. Marking client for deletion."
                )
                clients_to_be_deleted.append(client)
        # This was a client requested to us by the upstream community
        # that they are using. We should not delete it.
        # https://github.com/2i2c-org/infrastructure/issues/5496
        elif client["name"] != "VEDA Auth Prod":
            print(
                f"A cluster pertaining to client {client['name']} does NOT exist. Marking client for deletion."
            )
            clients_to_be_deleted.append(client)

    return clients_to_be_deleted


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


@cilogon_client_app.command()
def create(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        ..., help="Name of the hub for which we'll create a CILogon client"
    ),
    hub_domain: str = typer.Argument(
        ...,
        help="The hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud)",
    ),
):
    """Create a CILogon client for a hub."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    callback_url = f"https://{hub_domain}/hub/oauth_callback"
    create_client(admin_id, admin_secret, cluster_name, hub_name, callback_url)


@cilogon_client_app.command()
def update(
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


@cilogon_client_app.command()
def get(
    cluster_name: str = typer.Argument(..., help="Name of cluster to operate on"),
    hub_name: str = typer.Argument(
        ..., help="Name of the hub for which we'll retrieve the CILogon client details"
    ),
):
    """Retrieve details about an existing CILogon client."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    get_client(admin_id, admin_secret, cluster_name, hub_name)


@cilogon_client_app.command()
def get_all():
    """Retrieve details about all existing 2i2c CILogon clients."""
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    clients = get_all_clients(admin_id, admin_secret)
    for c in clients:
        print(c)

    # Our plan with CILogon only permits 100 clients, so provide feedback on that
    # number here. Change this if our plan updates.
    print_colour(f"{len(clients)} / 100 clients used", "yellow")


@cilogon_client_app.command()
def delete(
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
    """
    Delete an existing CILogon client. This deletes both the CILogon client application,
    and the client credentials from the configuration file.
    """
    config_filename = build_absolute_path_to_hub_encrypted_config_file(
        cluster_name, hub_name
    )
    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()

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

    delete_client(admin_id, admin_secret, cluster_name, hub_name, client_id)

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


@cilogon_client_app.command()
def cleanup(
    delete: bool = typer.Option(
        False, help="Proceed with deleting duplicated CILogon apps"
    )
):
    """Identify duplicated CILogon clients and which ID is being actively used in config,
    and optionally delete unused duplicates.

    Args:
        delete (bool, optional): Delete unused duplicate CILogon apps. Defaults to False.
    """
    clients_to_be_deleted = []

    admin_id, admin_secret = get_2i2c_cilogon_admin_credentials()
    clients = get_all_clients(admin_id, admin_secret)
    duplicated_clients = find_duplicated_clients(clients)

    # Cycle over each duplicated client name
    for duped_client in duplicated_clients:
        # Finds all the client IDs associated with a duplicated name
        ids = [c["client_id"] for c in clients if c["name"] == duped_client]

        # Establish the cluster and hub name from the client name and build the
        # absolute path to the encrypted hub values file
        cluster_name, hub_name = duped_client.split("-")
        config_filename = build_absolute_path_to_hub_encrypted_config_file(
            cluster_name, hub_name
        )

        with get_decrypted_file(config_filename) as decrypted_path:
            with open(decrypted_path) as f:
                secret_config = yaml.load(f)

        if (
            "CILogonOAuthenticator"
            not in secret_config["jupyterhub"]["hub"]["config"].keys()
        ):
            print(
                f"Hub {hub_name} on cluster {cluster_name} doesn't use CILogonOAuthenticator."
            )
        else:
            # Extract the client ID *currently in use* from the encrypted config and remove it from the list of IDs
            config_client_id = secret_config["jupyterhub"]["hub"]["config"][
                "CILogonOAuthenticator"
            ]["client_id"]
            ids.remove(config_client_id)

        clients_to_be_deleted.extend(
            [{"client_name": duped_client, "client_id": id} for id in ids]
        )

        # Remove the duplicated clients from the client list
        clients = [c for c in clients if c["name"] != duped_client]

    orphaned_clients = find_orphaned_clients(clients)
    clients_to_be_deleted.extend(orphaned_clients)

    print_colour("CILogon clients to be deleted...")
    for c in clients_to_be_deleted:
        print(c)

    if delete:
        for c in clients_to_be_deleted:
            delete_client(admin_id, admin_secret, client_id=c["client_id"])
