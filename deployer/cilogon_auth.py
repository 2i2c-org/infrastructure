from yarl import URL

import base64
import requests

class CILogonAdmin:
    timeout = 5.0

    def __init__(self, admin_id, admin_secret):
        self.admin_id = admin_id
        self.admin_secret = admin_secret

        bearer_token = base64.urlsafe_b64encode(f"{self.admin_id}:{self.admin_secret}")

        self.base_headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
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
        # todo: make this resilient, make use of exponentiall_backoff
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

        return self._post(self._url(), data=body)
    
    def get(self, id):
        """Retrieves a client by its id.

        Args:
           id (str): Id of the client to get

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-get.sh
        """

        return self.client.get(self._url(id))
    
    def update(self, id, body):
        """Modifies a client by its id.
        
        The client_secret attribute cannot be updated.
        Note that any values missing will be deleted from the information for the server!
        Args:
           id (str): Id of the client to modify
           body (dict): Attributes to modify.

        See: https://github.com/ncsa/OA4MP/blob/HEAD/oa4mp-server-admin-oauth2/src/main/scripts/oidc-cm-scripts/cm-put.sh
        """

        return self.client.put(self._url(id), data=body)


class ClientProvider:
    def __init__(self, admin_id, admin_secret):
        self.admin_id = admin_id
        self.admin_secret = admin_secret

    @property
    def cilogon(self):
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

        created_client = self.cilogon.create(client_details)

        return created_client
    
    def update_client(self, name, callback_url):
        client_details = {
            "client_name": name,
            "app_type": "web",
            "redirect_uris": [callback_url],
            "scope": "openid email org.cilogon.userinfo",
        }

        created_client = self.cilogon.update(client_details)

        return created_client

  
    def ensure_client(self, name, callback_url):
        client = self.get(name)

        if client is None or client["registration_client_uri"] is None:
            # Create the client, all good
            client = self.create_client(name, callback_url)
        else:
            # Update the client
            client = self.update_client(name, callback_url)

        return client

    def get_client_creds(self, client, connection_name):
        """
        Return z2jh config for cilogon authentication for this JupyterHub
        """

        auth = {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "username_claim": "nickname" if connection_name == "github" else "email",
            "scope": client["scope"],
            "logout_redirect_url": "https://cilogon.org/logout/",
            "allowed_idps": [connection_name]
        }

        return auth
