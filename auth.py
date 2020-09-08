import requests
from auth0.v3.management import Auth0
import os


class KeyProvider:
    def __init__(self, domain, auth0_token):
        self.auth0 = Auth0(domain, auth0_token)

    @property
    def clients(self):
        if not hasattr(self, '_clients'):
            self._clients = {
                client['name']: client
                for client in self.auth0.clients.all()
            }
        return self._clients

    def create_client(self, name, domain):
        client = {
            'name': name,
            'app_type': 'regular_web',
            'callbacks': [
                f'https://{domain}/hub/oauth_callback'
            ]
        }
        created_client = self.auth0.clients.create(client)
        self.clients[name] = created_client
        return created_client

    def update_client(self, client, domain):
        callback_url = f'https://{domain}/hub/oauth_callback'
        if 'callbacks' not in client or callback_url not in client['callbacks']:
            self.auth0.clients.update(
                client['client_id'],
                {
                    'callbacks': [callback_url]
                }
            )

    def get_client_creds(self, name, domain):
        if name not in self.clients:
            client = self.create_client(name, domain)
        else:
            client = self.clients[name]
        self.update_client(client, domain)
        return {
            'client_id': client['client_id'],
            'client_secret': client['client_secret']
        }
