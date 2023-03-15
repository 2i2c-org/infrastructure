# Auth0

```{warning}
This authentication method is now deprecated and should only be used if absolutely necessary.
Please use [](auth:cilogon) instead.
```

[`auth0`](https://auth0.com) can be configured with many different [connections](https://auth0.com/docs/identityproviders) that users can authenticate with - such as Google, GitHub, etc.

:::{note}
If you wish to authenticate users based on their membership in a GitHub organization or team, you'll need to use [the native GitHub OAuthenticator instead](auth:github-orgs).
:::

So we want to manage authentication by:

1. **Create an Auth0 client and configure it**
   This can be achieved by using the `deployer auth0-client-create` command.

   - The command needs to be passed the cluster and hub name for which a client id and secret will be generated, but also the hub type, the hub domain, and the connection type.
     Currently common ones are `google-oauth2` for Google & `github` for GitHub. *Users* of the hub will use this method to log in to the hub.
     Theoretically, every provider in [this list](https://auth0.com/docs/connections/identity-providers-social) is supported. However, we've currently only tested this with Google(`google-oauth2`) and GitHub (`github`)


   - Example script invocation that creates an Auth0 client for the 2i2c dask-staging hub and configures Auth0 to use GitHub as a connection is:

      ```bash
      deployer cilogon-client-create create 2i2c dask-staging daskhub dask-staging.2i2c.cloud github
      ```

   - If successful, the script will have created a secret values file under `config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml`. This file holds the encrypted OAuth client id and secret that have been created for this hub, but also all the other config needed for the hub **for simplicity**.

   - The unencrypted file contents should look like this:
      ```yaml
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: auth0
              Auth0OAuthenticator:
               auth0_subdomain: 2i2c.us
               userdata_url: https://{domain}/userinfo,
               username_key: github,
               client_id: CLIENT_ID,
               client_secret: CLIENT_SECRET,
               scope: ["openid", "name", "profile", "email"],
               logout_redirect_url: LOGOUT_URL
        ```

2. Explicitly list *admin users* for a given hub. These admin users will be the
   only ones allowed to log in to begin with. They can use the JupyterHub
   admin interface (available from their hub control panel) to explicitly allow
   more users into the hub. This way, we don't need to be involved in explicitly
   allowing users into hubs.

   In the admin interface, admin users can add users via a username appropriate
   for the auth connector used. For GitHub, it's the username. For Google Auth,
   it's the email address.

   You can set the admin interfaces for a hub like this:

   ```yaml
   jupyterhub:
     auth:
       allowed_users:
           # WARNING: THESE USER LISTS MUST MATCH (for now)
           - user1@gmail.com
           - user2@gmail.com
       admin_users:
           # WARNING: THESE USER LISTS MUST MATCH (for now)
           - user1@gmail.com
           - user2@gmail.com
   ```
