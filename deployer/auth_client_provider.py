class ClientProvider:
    @property
    def admin_client(self):
        """Return an administrative instance of the authentication client.

        This instance must be able to create/update/delete other clients.
        """

        pass

    def create_client(self, name, callback_url, logout_url):
        """Create a OAuth2 client application.

        **Subclasses must define this method**

        Args:
            name (str): human readable name of the client
            callback_url (str): URL that is invoked after OAuth authorization
            logout_url (string): URL to redirect users to after app logout
        """
        pass

    def ensure_client(
        self,
        name,
        callback_url,
        logout_url,
        allowed_connections,
        connection_config,
    ):
        """Ensures a client with the specified name and config exists.
        If one doesn't exist, create it and if it does exist, update it
        with the specified config.

        **Subclasses must define this method**

        Args:
            name (str): human readable name of the client
            callback_url (str): URL that is invoked after OAuth authorization
            logout_url (string): URL to redirect users to after app logout
            allowed_connections: A single string or a list of strings representing the
                connections/identity providers the client should accept
            connection_config: Extra configuration to be passed to the chosen connection/s

        Should return a dict describing the client created/updated.

        """
        raise NotImplementedError

    def get_client_creds(self, client, allowed_connections, callback_url):
        """Return z2jh config for auth0 authentication for this JupyterHub.

        Args:
            client (dict): OAuth2 clientvv - must include `client_id` and `client_secret` keys
            callback_url (str): URL that is invoked after OAuth authorization
            allowed_connections: A single string or a list of strings representing the
                allowed connections/identity providers
        """

        raise NotImplementedError
