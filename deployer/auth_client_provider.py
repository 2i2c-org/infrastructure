class ClientProvider:
    @property
    def admin_client(self):
        """Return an administrative instance of the authentication client.

        This instance must be able to create/update/delete other clients.
        """

        pass

    def create_client(self, name, callback_url, logout_url=None):
        """Create a OAuth2 client application.

        **Subclasses must define this method**

        Args:
            name (str): human readable name of the client
            callback_url (str): URL that is invoked after OAuth authorization 
            (optional) logout_url (string): URL to redirect users to after app logout
        """
        pass

    def ensure_client(
        self, name, callback_url, logout_url=None, connection_name=None, connection_config=None
    ):
        """Ensures a client with the specified name and config exists.
        If one doesn't exist, create it and if it does exist, update it
        with the specified config.
        
        **Subclasses must define this method**

        Args:
            name (str): human readable name of the client
            callback_url (str): URL that is invoked after OAuth authorization 
            (optional) logout_url (string): URL to redirect users to after app logout
            (optional) connection_name: The name of the connection/identity provider
            (optional) connection_config: Extra configuration to be passed to the chosen connection
        
        Should return a dict describing the client created/updated.

        """
        pass

    def get_client_creds(self, client, connection_name=None, callback_url=None):
        """Return z2jh config for auth0 authentication for this JupyterHub.

        Args:
            client (dict): OAuth2 clientvv - must include `client_id` and `client_secret` keys
            (optional) callback_url (str): URL that is invoked after OAuth authorization 
            (optional) connection_name: The name of the connection/identity provider
        """

        pass