import requests
from auth0.v3.management import Auth0
from auth0.v3.authentication import GetToken
from auth0.v3.management import Rules
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

    def create_google_domain_rule(self, hub_name, domain_list, admin_list):
        gt = GetToken(self.domain)
        creds = gt.client_credentials(
            self.client_id, self.client_secret,
            f'https://{self.domain}/api/v2/'
        )
        rules = Rules(self.domain, creds['access_token'])
        existing_rules = rules.all(enabled=False, fields=['name', 'order'])
        print(existing_rules)

        rule_name = "Domain allowed list for {} hub".format(hub_name)

        rule_exists = False
        rule_max_idx = 0
        for rule in existing_rules:
            if rule['order'] > rule_max_idx:
                rule_max_idx = rule['order']
            if rule['name'] == rule_name:
                rule_exists = True

        if not rule_exists:
            rule = "function emailDomainAllowedList(user, context, callback) {{\n if (!user.email || !user.email_verified) {{\n return callback(new UnauthorizedError('Access denied.')); \n }}\n if(context.clientName !== {}){{\n return callback(null, user, context);\n }}\n const domainAllowedList = {};\n const userHasDomainAccess = domainAllowedList.some(function (domain) {{\n const emailSplit = user.email.split('@');\n return emailSplit[emailSplit.length - 1].toLowerCase() === domain;\n }});\n const adminList = {}; // authorized admin users outside of the allowed domains\n const userIsAdmin = adminList.some(function (email) {{\n return email === user.email;\n }});\n const userHasAccess = userHasDomainAccess || userIsAdmin;\n if (!userHasAccess) {{\n return callback(new UnauthorizedError('Access denied.'));\n }}\n return callback(null, user, context);\n }}"
            request_body = {
                "name": rule_name,
                "script": rule.format(hub_name, domain_list, admin_list),
                "order": rule_max_idx + 1,
                "enabled": False
            }
            resp = rules.create(request_body)
            return resp
        else:
            print("A rule with this name already exists. Skipping rule creation...")

        
    def get_client_creds(self, client, connection_name):
        """
        Return z2jh config for auth0 authentication for this JupyterHub
        """

        # default to using emails as usernames
        username_key = 'email'
        if connection_name == 'github':
            # Except for GitHub, where we use the username
            username_key = 'nickname'
        auth = {}
        auth['scopes'] = ['openid', 'name', 'profile', 'email']
        auth['type'] = 'custom'
        auth['custom'] = {
            'className': 'oauthenticator.generic.GenericOAuthenticator',
            'config': {
                'authorize_url': f'https://{self.domain}/authorize',
                'token_url': f'https://{self.domain}/oauth/token',
                'userdata_url': f'https://{self.domain}/userinfo',
                'userdata_method': 'GET',
                'username_key': username_key,
                'client_id': client['client_id'],
                'client_secret': client['client_secret']
            }

        }

        return auth
