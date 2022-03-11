import base64
import requests
import subprocess

from ruamel.yaml import YAML
from yarl import URL

from auth_client_provider import ClientProvider
from file_acquisition import get_decrypted_file

yaml = YAML(typ="safe")

class CILogonAdmin:
    timeout = 5.0

    def __init__(self, admin_id, admin_secret):
        self.admin_id = admin_id
        self.admin_secret = admin_secret

        token_string = f"{self.admin_id}:{self.admin_secret}"
        bearer_token = base64.urlsafe_b64encode(token_string.encode('utf-8')).decode('ascii')

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
        # todo: make this resilient, use of an exponentiall backoff
        headers = self.base_headers.copy()

        return requests.get(url, params=params, headers=headers, timeout=self.timeout)
    
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
        if response.status_code != 200:
            return

        return response.json()
    
    def get(self, id):
        """Retrieves a client by its id.

        Args:
           id (str): Id of the client to get

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-get.sh
        """

        response = self._get(self._url(id))
        if response.status_code != 200:
            return

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
        if response.status_code != 200:
            return

        return response.json()


class CILogonClientProvider(ClientProvider):
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

    def create_client(self, name, callback_url):
        client_details = {
            "client_name": name,
            "app_type": "web",
            "redirect_uris": [callback_url],
            "scope": "openid email org.cilogon.userinfo",
        }

        return self.admin_client.create(client_details)
    
    def update_client(self, client_id, name, callback_url):
        client_details = {
            "client_name": name,
            "app_type": "web",
            "redirect_uris": [callback_url],
            "scope": "openid email org.cilogon.userinfo",
        }

        return self.admin_client.update(client_id, client_details)

  
    def ensure_client(
        self, name, callback_url, logout_url=None, connection_name=None, connection_config=None
    ):
        client_id = None
        try:
            with get_decrypted_file(connection_config) as decrypted_path:
                with open(decrypted_path) as f:
                    cilogon_clients = yaml.load(f)
            cilogon_client= cilogon_clients.get(name, None)
            client_id = cilogon_client["client_id"]
        except FileNotFoundError:
            cilogon_clients = {}
            client_id = None
        finally:
            if client_id is None:
                # Create the client, all good
                client = self.create_client(name, callback_url)
                cilogon_clients[name] = {
                    "client_id": client["client_id"],
                    "client_secret": client["client_id"]
                }
                # persist the client id
                # todo: use a semaphore when we'll deploy hubs in parallel
                with open(connection_config, "w+") as f:
                    yaml.dump(cilogon_clients, f)
                subprocess.check_call(
                    ["sops", "--encrypt", "--in-place", connection_config]
                )
            else:
                client = self.update_client(client_id, name, callback_url)
                # CILogon doesn't return the client secret after its creation
                client["client_secret"] = cilogon_clients[name]["client_secret"]

        return client

    def get_client_creds(self, client, connection_name, callback_url):
        """
        Return z2jh config for cilogon authentication for this JupyterHub
        """

        auth = {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "username_claim": "email",
            "scope": client["scope"],
            "oauth_callback_url": callback_url,
            "logout_redirect_url": "https://cilogon.org/logout/",
            "allowed_idps": [connection_name]
        }

        return auth
