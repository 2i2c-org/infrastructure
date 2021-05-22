from auth0.v3.authentication import GetToken
from auth0.v3.management import Auth0

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

    def create_client(self, name, domains):
        callbacks = self._get_callback_url_list(domains)
        logout_urls = self._get_allowed_logout_url_list(domains)

        client = {
            'name': name,
            'app_type': 'regular_web',
            'callbacks': callbacks,
            'allowed_logout_urls': logout_urls
        }
        created_client = self.auth0.clients.create(client)
        return created_client

    def _get_callback_url_list(self, domains):
        return [f'https://{domain}/hub/oauth_callback' for domain in domains] if isinstance(domains, list) else [f'https://{domains}/hub/oauth_callback']

    def _get_allowed_logout_url_list(self, domains):
        return [f'https://{domain}/hub/' for domain in domains] if isinstance(domains, list) else [f'https://{domains}/hub/']


    def _ensure_client_callback(self, client, domains):
        callback_urls = self._get_callback_url_list(domains)
        missing_callbacks = []

        for callback_url in callback_urls:
            if 'callbacks' not in client or callback_url not in client['callbacks']:
                missing_callbacks.append(callback_url)

        if missing_callbacks:
            self.auth0.clients.update(
                client['client_id'],
                {
                    # Don't remove other callback URLs
                    'callbacks': client['callbacks'] + missing_callbacks
                }
            )

    def _ensure_client_logout_urls(self, client, domains):
        logout_urls = self._get_allowed_logout_url_list(domains)
        missing_logout_urls = []

        for logout_url in logout_urls:
            if 'allowed_logout_urls' not in client or logout_url not in client['allowed_logout_urls']:
                missing_logout_urls.append(logout_url)

        if missing_logout_urls:
            self.auth0.clients.update(
                client['client_id'],
                {
                    # Don't remove other logout URLs
                    'allowed_logout_urls': client.get('allowed_logout_urls', []) + missing_logout_urls
                }
            )


    def ensure_client(self, name, domains, connection_name):
        current_clients = self.get_clients()
        if name not in current_clients:
            # Create the client, all good
            client = self.create_client(name, domains)
        else:
            client = current_clients[name]
            self._ensure_client_callback(client, domains)
            self._ensure_client_logout_urls(client, domains)

        current_connections = self.get_connections()

        if connection_name == 'password':
            # Users should not be shared between hubs - each hub
            # should have its own username / password database.
            # So we create a new 'database connection' per hub,
            # instead of sharing one across hubs.
            db_connection_name = f'database-{name}'

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

        auth = {
            'authorize_url': f'https://{self.domain}/authorize',
            'token_url': f'https://{self.domain}/oauth/token',
            'userdata_url': f'https://{self.domain}/userinfo',
            'userdata_method': 'GET',
            'username_key': USERNAME_KEYS[connection_name],
            'client_id': client['client_id'],
            'client_secret': client['client_secret'],
            'scope': ['openid', 'name', 'profile', 'email'],
            'logout_redirect_url': f'https://{self.domain}/v2/logout?client_id={client["client_id"]}'
        }

        return auth
