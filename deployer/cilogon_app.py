import argparse
import base64
import requests
import subprocess
import time

from pathlib import Path
from ruamel.yaml import YAML
from yarl import URL

from file_acquisition import find_absolute_path_to_cluster_file, get_decrypted_file

yaml = YAML(typ="safe")


class CILogonAdmin:
    timeout = 5.0

    def __init__(self, admin_id, admin_secret):
        self.admin_id = admin_id
        self.admin_secret = admin_secret

        token_string = f"{self.admin_id}:{self.admin_secret}"
        bearer_token = base64.urlsafe_b64encode(token_string.encode("utf-8")).decode(
            "ascii"
        )

        self.base_headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _url(self, id=None):
        url = "https://cilogon.org/oauth2/oidc-cm"

        if id is None:
            return url

        return str(URL(url).with_query({"client_id": id}))

    def _post(self, url, data=None):
        headers = self.base_headers.copy()

        return requests.post(url, json=data, headers=headers, timeout=self.timeout)

    def _get(self, url, params=None):
        headers = self.base_headers.copy()

        timeout = time.time() + 10
        t = 0.05

        # Allow up to 10s of retrying getting the response
        while time.time() < timeout:
            response = requests.get(
                url, params=params, headers=headers, timeout=self.timeout
            )
            if response.status_code == 200:
                return response

            t = min(2, t * 2)
            time.sleep(t)

        # Return latest response to the request
        return response

    def _put(self, url, data=None):
        headers = self.base_headers.copy()

        return requests.put(url, json=data, headers=headers, timeout=self.timeout)

    def create(self, body):
        """Creates a new client

        Args:
           body (dict): Attributes for the new client

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-post.sh
        """

        response = self._post(self._url(), data=body)
        client_name = body["client_name"]

        if response.status_code != 200:
            print(
                f"An error occured when creating the {client_name} client. \n Error was {response.text}."
            )
            response.raise_for_status()

        print(f"Successfully created a new CILogon client for {client_name}!")
        return response.json()

    def get(self, id):
        """Retrieves a client by its id.

        Args:
           id (str): Id of the client to get

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-get.sh
        """

        response = self._get(self._url(id))

        if response.status_code != 200:
            print(
                f"An error occured when getting the details of {id} client. \n Error was {response.text}."
            )
            response.raise_for_status()

        print(f"Successfully got the details for {id} client!")
        return response.json()

    def update(self, id, body):
        """Modifies a client by its id.

        The client_secret attribute cannot be updated.
        Note that any values missing will be deleted from the information for the server!
        Args:
           id (str): Id of the client to modify
           body (dict): Attributes to modify.

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-put.sh
        """
        response = self._put(self._url(id), data=body)
        client_name = body["client_name"]

        if response.status_code != 200:
            print(
                f"An error occured when updating the {client_name} client. \n Error was {response.text}."
            )
            response.raise_for_status()

        print("Client updated succesfuly!")
        return response.status_code


class CILogonClientProvider:
    def __init__(self, admin_id, admin_secret):
        self.admin_id = admin_id
        self.admin_secret = admin_secret

    @property
    def admin_client(self):
        """
        Return a CILogonAdmin instance
        """
        if not hasattr(self, "_cilogon_admin"):
            self._cilogon_admin = CILogonAdmin(self.admin_id, self.admin_secret)

        return self._cilogon_admin

    def _build_client_details(self, cluster_name, hub_name, callback_url):
        client_details = {
            "client_name": f"{cluster_name}-{hub_name}",
            "app_type": "web",
            "redirect_uris": [callback_url],
            "scope": "openid email org.cilogon.userinfo",
        }

        return client_details

    def _build_config_filename(self, cluster_name, hub_name):
        cluster_config_dir_path = find_absolute_path_to_cluster_file(
            cluster_name
        ).parent

        return cluster_config_dir_path.joinpath(f"enc-{hub_name}.secret.values.yaml")

    def _persist_client_credentials(self, client, hub_type, config_filename):
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

        if hub_type != "basehub":
            auth_config["basehub"] = jupyterhub_config
        else:
            auth_config = jupyterhub_config

        with open(config_filename, "w+") as f:
            yaml.dump(auth_config, f)
        subprocess.check_call(["sops", "--encrypt", "--in-place", config_filename])

    def _load_client_id(self, config_filename):
        try:
            with get_decrypted_file(config_filename) as decrypted_path:
                with open(decrypted_path) as f:
                    auth_config = yaml.load(f)

            basehub = auth_config.get("basehub", None)
            if basehub:
                return auth_config["basehub"]["jupyterhub"]["hub"]["config"][
                    "CILogonOAuthenticator"
                ]["client_id"]
            return auth_config["jupyterhub"]["hub"]["config"]["CILogonOAuthenticator"][
                "client_id"
            ]
        except FileNotFoundError:
            print(
                "The CILogon client you requested to update doesn't exist! Please create it first."
            )

    def create_client(self, cluster_name, hub_name, hub_type, callback_url):
        client_details = self._build_client_details(
            cluster_name, hub_name, callback_url
        )
        config_filename = self._build_config_filename(cluster_name, hub_name)

        if Path(config_filename).is_file():
            print(
                f"""
                Oops! A CILogon client already exists for this hub!
                Use the update subcommand to update it or delete {config_filename} if you want to generate a new one.
                """
            )
            return

        # Ask CILogon to create the client
        print(f"Creating client with details {client_details}...")
        client = self.admin_client.create(client_details)

        # Persist and encrypt the client credentials
        self._persist_client_credentials(client, hub_type, config_filename)
        print(f"Client credentials encrypted and stored to {config_filename}.")

    def update_client(self, cluster_name, hub_name, callback_url):
        client_details = self._build_client_details(
            cluster_name, hub_name, callback_url
        )
        config_filename = self._build_config_filename(cluster_name, hub_name)

        if not Path(config_filename).is_file():
            print(
                "Oops! No CILogon client has been found for this hub! Use the create subcommand to create one."
            )
            return

        client_id = self._load_client_id(config_filename)

        print(f"Updating the existing CILogon client for {cluster_name}-{hub_name}...")
        return self.admin_client.update(client_id, client_details)

    def get_client(self, cluster_name, hub_name):
        config_filename = self._build_config_filename(cluster_name, hub_name)

        if not Path(config_filename).is_file():
            print(
                "Oops! No CILogon client has been found for this hub! Use the `create` command to create one."
            )
            return

        client_id = self._load_client_id(config_filename)

        print(
            f"Getting the stored CILogon client details for {cluster_name}-{hub_name}..."
        )
        print(self.admin_client.get(client_id))


def main():
    argparser = argparse.ArgumentParser(
        description="""A command line tool to create/update/delete
        CILogon clients.
        """
    )
    subparsers = argparser.add_subparsers(
        required=True, dest="action", help="Available subcommands"
    )

    # Create subcommand
    create_parser = subparsers.add_parser(
        "create",
        help="Create a CILogon client",
    )

    create_parser.add_argument(
        "cluster_name",
        type=str,
        help="The name of the cluster where the hub lives",
    )

    create_parser.add_argument(
        "hub_name",
        type=str,
        help="The hub for which we'll create a CILogon client",
    )

    create_parser.add_argument(
        "hub_type",
        type=str,
        help="The type of hub for which we'll create a CILogon client.",
        default="basehub",
    )

    create_parser.add_argument(
        "callback_url",
        type=str,
        help="URL that is invoked after OAuth authorization",
    )

    # Update subcommand
    update_parser = subparsers.add_parser(
        "update",
        help="Update a CILogon client",
    )

    update_parser.add_argument(
        "cluster_name",
        type=str,
        help="The name of the cluster where the hub lives",
    )

    update_parser.add_argument(
        "hub_name",
        type=str,
        help="The hub for which we'll update the CILogon client",
    )

    update_parser.add_argument(
        "callback_url",
        type=str,
        help="""
        New callback_url to associate with the client.
        This URL is invoked after OAuth authorization
        """,
    )

    # Get subcommand
    get_parser = subparsers.add_parser(
        "get",
        help="Retrieve details about an existing CILogon client",
    )

    get_parser.add_argument(
        "cluster_name",
        type=str,
        help="The name of the cluster where the hub lives",
    )

    get_parser.add_argument(
        "hub_name",
        type=str,
        help="The hub for which we'll retrieve the CILogon client details.",
    )

    args = argparser.parse_args()

    # This filepath is relative to the PROJECT ROOT
    general_auth_config = "shared/deployer/enc-auth-providers-credentials.secret.yaml"
    with get_decrypted_file(general_auth_config) as decrypted_file_path:
        with open(decrypted_file_path) as f:
            config = yaml.load(f)

    cilogon = CILogonClientProvider(
        config["cilogon_admin"]["client_id"], config["cilogon_admin"]["client_secret"]
    )

    if args.action == "create":
        cilogon.create_client(
            args.cluster_name,
            args.hub_name,
            args.hub_type,
            args.callback_url,
        )
    elif args.action == "update":
        cilogon.update_client(
            args.cluster_name,
            args.hub_name,
            args.callback_url,
        )
    elif args.action == "get":
        cilogon.get_client(
            args.cluster_name,
            args.hub_name,
        )


if __name__ == "__main__":
    main()
