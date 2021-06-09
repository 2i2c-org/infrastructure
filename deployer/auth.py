from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0

from yarl import URL
import re

# What key in the authenticated user's profile to use as hub username
# This shouldn't be changeable by the user!
USERNAME_KEYS = {
    'github': 'nickname',
    'google-oauth2': 'email',
    'ORCID': 'sub',
    'password': 'email'
}


class KeyProvider:
    def __init__(self, domain, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain = domain

    @property
    def auth0(self):
        """
        Return an authenticated Auth0 instance
        """
        if not hasattr(self, '_auth0'):
            gt = GetToken(self.domain)
            creds = gt.client_credentials(
                self.client_id, self.client_secret,
                f'https://{self.domain}/api/v2/'
            )
            self._auth0 = Auth0(self.domain, creds['access_token'])
        return self._auth0

    def get_clients(self):
        return {
            client['name']: client
            for client in self.auth0.clients.all()
        }

    def get_connections(self):
        return {
            connection['name']: connection
            for connection in self.auth0.connections.all()
        }

    def create_client(self, name, callback_url, logout_url):
        client = {
            'name': name,
            'app_type': 'regular_web',
            'callbacks': [callback_url],
            'allowed_logout_urls': [logout_url]
        }
        created_client = self.auth0.clients.create(client)
        return created_client


    def _ensure_client_callback(self, client, callback_url):
        """
        Ensure client has correct callback URL
        """
        if client['callbacks'] != [callback_url]:
            self.auth0.clients.update(
                client['client_id'],
                {
                    # Overwrite any other callback URL specified
                    # Only one hub should use any one auth0 application, and it
                    # should only have one callback url. Additional URLs can be
                    # a security risk, since people who control those URLs could
                    # potentially steal user credentials (if they have client_id and secret).
                    # Fully managing list of callback URLs in code keeps everything
                    # simpler
                    'callbacks': [callback_url]
                }
            )

    def _ensure_client_logout_url(self, client, logout_url):
        if client['allowed_logout_urls'] != [logout_url]:
            self.auth0.clients.update(
                client['client_id'],
                {
                    # Overwrite any other logout URL - users should only land on
                    # the hug home page after logging out.
                    'allowed_logout_urls': [logout_url]
                }
            )

    def ensure_client(self, name, callback_url, logout_url, connection_name, connection_config):
        current_clients = self.get_clients()
        if name not in current_clients:
            # Create the client, all good
            client = self.create_client(name, callback_url, logout_url)
        else:
            client = current_clients[name]
            self._ensure_client_callback(client, callback_url)
            self._ensure_client_logout_url(client, logout_url)

        current_connections = self.get_connections()

        if connection_name == 'password':
            # Users should not be shared between hubs - each hub
            # should have its own username / password database.
            # So we create a new 'database connection' per hub,
            # instead of sharing one across hubs.
            db_connection_name = connection_config.get("database_name", name)

            if db_connection_name not in current_connections:
                # connection doesn't exist yet, create it
                connection = self.auth0.connections.create({
                    'name': db_connection_name,
                    'display_name': name,
                    'strategy': 'auth0'
                })
                current_connections[db_connection_name] = connection
            selected_connection_name = db_connection_name
        else:
            selected_connection_name = connection_name

        for connection in current_connections.values():
            # The chosen connection!
            enabled_clients = connection['enabled_clients'].copy()
            needs_update = False
            client_id = client['client_id']
            if connection['name'] == selected_connection_name:
                if client_id not in enabled_clients:
                    enabled_clients.append(client_id)
                    needs_update = True
            else:
                if client_id in enabled_clients:
                    enabled_clients.remove(client_id)
                    needs_update = True

            if needs_update:
                self.auth0.connections.update(
                    connection['id'],
                    {'enabled_clients': enabled_clients}
                )

        return client


    def get_client_creds(self, client, connection_name):
        """
        Return z2jh config for auth0 authentication for this JupyterHub
        """

        logout_redirect_params = {
            'client_id': client["client_id"],
            'returnTo': client["allowed_logout_urls"][0]
        }

        auth = {
            'auth0_subdomain': re.sub('\.auth0.com$', '', self.domain),
            'userdata_url': f'https://{self.domain}/userinfo',
            'username_key': USERNAME_KEYS[connection_name],
            'client_id': client['client_id'],
            'client_secret': client['client_secret'],
            'scope': ['openid', 'name', 'profile', 'email'],
            'logout_redirect_url': str(URL(f'https://{self.domain}/v2/logout').with_query(logout_redirect_params))
        }

        return auth
