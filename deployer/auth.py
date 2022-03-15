import re

from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0
from yarl import URL

from auth_client_provider import ClientProvider

# What key in the authenticated user's profile to use as hub username
# This shouldn't be changeable by the user!
USERNAME_KEYS = {
    "github": "nickname",
    "google-oauth2": "email",
    "password": "email",
    "CILogon": "email",
}


class Auth0ClientProvider(ClientProvider):
    def __init__(self, client_id, client_secret, domain):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain

    @property
    def admin_client(self):
        """
        Return an authenticated Auth0 instance
        """
        if not hasattr(self, "_admin_client"):
            gt = GetToken(self.domain)
            creds = gt.client_credentials(
                self.client_id, self.client_secret, f"https://{self.domain}/api/v2/"
            )
            self._admin_client = Auth0(self.domain, creds["access_token"])
        return self._admin_client

    def _get_clients(self):
        return {
            client["name"]: client
            # Our account is limited to 100 clients, and we want it all in one go
            for client in self.admin_client.clients.all(per_page=100)
        }

    def _get_connections(self):
        return {
            connection["name"]: connection
            for connection in self.admin_client.connections.all()
        }

    def create_client(self, name, callback_url, logout_url):
        client = {
            "name": name,
            "app_type": "regular_web",
            "callbacks": [callback_url],
            "allowed_logout_urls": [logout_url],
        }
        created_client = self.admin_client.clients.create(client)
        return created_client

    def _ensure_client_callback(self, client, callback_url):
        """
        Ensure client has correct callback URL
        """
        if "callbacks" not in client or client["callbacks"] != [callback_url]:
            self.admin_client.clients.update(
                client["client_id"],
                {
                    # Overwrite any other callback URL specified
                    # Only one hub should use any one auth0 application, and it
                    # should only have one callback url. Additional URLs can be
                    # a security risk, since people who control those URLs could
                    # potentially steal user credentials (if they have client_id and secret).
                    # Fully managing list of callback URLs in code keeps everything
                    # simpler
                    "callbacks": [callback_url]
                },
            )

    def _ensure_client_logout_url(self, client, logout_url):
        if "allowed_logout_urls" not in client or client["allowed_logout_urls"] != [
            logout_url
        ]:
            self.admin_client.clients.update(
                client["client_id"],
                {
                    # Overwrite any other logout URL - users should only land on
                    # the hub home page after logging out.
                    "allowed_logout_urls": [logout_url]
                },
            )

    def ensure_client(
        self,
        name,
        callback_url,
        logout_url,
        allowed_connections: str,
        connection_config,
    ):
        # Our Auth0 setup currently suports only one connection, so this must be a string!
        connection_name = allowed_connections

        current_clients = self._get_clients()
        if name not in current_clients:
            # Create the client, all good
            client = self.create_client(name, callback_url, logout_url)
        else:
            client = current_clients[name]
            self._ensure_client_callback(client, callback_url)
            self._ensure_client_logout_url(client, logout_url)

        current_connections = self._get_connections()

        if connection_name == "password":
            # Users should not be shared between hubs - each hub
            # should have its own username / password database.
            # So we create a new 'database connection' per hub,
            # instead of sharing one across hubs.
            db_connection_name = connection_config.get("database_name", name)

            if db_connection_name not in current_connections:
                # connection doesn't exist yet, create it
                connection = self.admin_client.connections.create(
                    {
                        "name": db_connection_name,
                        "display_name": name,
                        "strategy": "auth0",
                    }
                )
                current_connections[db_connection_name] = connection
            selected_connection_name = db_connection_name
        else:
            selected_connection_name = connection_name

        for connection in current_connections.values():
            # The chosen connection!
            enabled_clients = connection["enabled_clients"].copy()
            needs_update = False
            client_id = client["client_id"]
            if connection["name"] == selected_connection_name:
                if client_id not in enabled_clients:
                    enabled_clients.append(client_id)
                    needs_update = True
            else:
                if client_id in enabled_clients:
                    enabled_clients.remove(client_id)
                    needs_update = True

            if needs_update:
                self.admin_client.connections.update(
                    connection["id"], {"enabled_clients": enabled_clients}
                )

        return client

    def get_client_creds(self, client, allowed_connections: str, callback_url):
        # Our Auth0 setup currently suports only one connection, so this must be a string!
        connection_name = allowed_connections

        logout_redirect_params = {
            "client_id": client["client_id"],
            "returnTo": client["allowed_logout_urls"][0],
        }

        auth = {
            "auth0_subdomain": re.sub(r"\.auth0.com$", "", self.domain),
            "userdata_url": f"https://{self.domain}/userinfo",
            "username_key": USERNAME_KEYS[connection_name],
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "scope": ["openid", "name", "profile", "email"],
            "logout_redirect_url": str(
                URL(f"https://{self.domain}/v2/logout").with_query(
                    logout_redirect_params
                )
            ),
        }

        return auth
