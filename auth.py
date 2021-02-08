import requests
from auth0.v3.management import Auth0
from auth0.v3.authentication import GetToken
import os


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

    def create_client(self, name, domain):
        client = {
            'name': name,
            'app_type': 'regular_web',
            'callbacks': [
                f'https://{domain}/hub/oauth_callback'
            ]
        }
        created_client = self.auth0.clients.create(client)
        return created_client

    def _ensure_client_callback(self, client, domain):
        callback_url = f'https://{domain}/hub/oauth_callback'
        if 'callbacks' not in client or callback_url not in client['callbacks']:
            self.auth0.clients.update(
                client['client_id'],
                {
                    # Don't remove other callback URLs
                    'callbacks': client['callbacks'] + [callback_url]
                }
            )

    def ensure_client(self, name, domain, connection_name):
        current_clients = self.get_clients()
        if name not in current_clients:
            # Create the client, all good
            client = self.create_client(name, domain)
        else:
            client = current_clients[name]
            self._ensure_client_callback(client, domain)

        current_connections = self.get_connections()
        for connection in current_connections.values():
                # The chosen connection!
            enabled_clients = connection['enabled_clients'].copy()
            needs_update = False
            client_id = client['client_id']
            if connection['name'] == connection_name:
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

        # default to using emails as usernames
        username_key = 'email'
        if connection_name == 'github':
            # Except for GitHub, where we use the username
            username_key = 'nickname'
        auth = {
            'authorize_url': f'https://{self.domain}/authorize',
            'token_url': f'https://{self.domain}/oauth/token',
            'userdata_url': f'https://{self.domain}/userinfo',
            'userdata_method': 'GET',
            'username_key': username_key,
            'client_id': client['client_id'],
            'client_secret': client['client_secret'],
            'scopes': ['openid', 'name', 'profile', 'email']
        }

        return auth
