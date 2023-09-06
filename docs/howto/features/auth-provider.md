# Providing credentials for externally managed services

Sometimes, our communities want to run *their own* [external JupyterHub service](https://jupyterhub.readthedocs.io/en/stable/reference/services.html#externally-managed-services),
often just to use JupyterHub as an OAuth2 provider for user logins. This
allows them to have the same shared users between the hub and their 
service.

2i2c can not manage such external services, but we will provide
appropriate credentials to them so they can do so themselves.

## Setting up service credentials

1. Define the service in the appropriate hub's `<hub-name>.values.yaml` file:

   ```yaml
   jupyterhub:
     hub:
       services:
         # Name of the service should be provided to us by the community
         <name-of-service>:
           name: <name-of-service>
           # The client_id for this service - it *must* start with service-
           oauth_client_id: service-<name-of-service>
           # The OAuth2 redirect URI provided to us by the community
           oauth_redirect_uri: <oauth-redirect-uri>
           # Set to true if it should be displayed under 'services' in the
           # hub control panel
           display: true/false
           # Set this to false if there should be an extra 'do you want to
           # approve this external service?' authorization screen. For external
           # services, we mostly don't want it - so let's set this to true
           oauth_no_confirm: true
       config:
         # This prevents the hub home page from showing when the end user
         # tries to authenticate with the hub from the external service.
         # Since the hub might send the user to CILogon or GitHub or another
         # auth service, removing this step makes the flow smoother.
         auto_login_oauth2_authorize: true
   ```


2. Generate an appropriate OAuth2 client secret on the commandline by running
   `openssl rand -hex 32`
   
3. Define appropriate secrets in the hub's `enc-<hub-name>.secret.values.yaml` file:

   ```yaml
   jupyterhub:
     hub:
       services:
         <name-of-service>:
           # This will be the client secret
           api_token: <output-of-step-2> 
   ```
           
4. Commit and deploy this.

5. Send our community the following pieces of information to configure their
   OAuth2 *client* with:
   
   ```
   client_id: <oauth_client_id_from_step_1>
   client_secret: <api_key_from_step_3>
   authorization_url: https://<hub-domain>/hub/api/oauth2/authorize
   token_url: https://<hub-domain>/hub/api/oauth2/token
   userinfo_url: https://<hub-domain>/hub/api/user
   ```
   
   In addition, the following pieces of information would be useful:
   
   a. The `client_secret` **must** be sent as a token in the `Authorization` header when making the token request to the `token_url`.
   b. The `name` field from the user profile contains the user's name on the hub.
   
   This should be enough information for them to configure their oauth2 client to authenticate
   against the JupyterHub!
