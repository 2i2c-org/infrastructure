(auth:cilogon)=
# CILogon
2i2c manages CILogon using the JupyterHub CILogonOAuthenticator.

## Enable and configure the JupyterHub CILogonOAuthenticator for a hub

The steps to enable the JupyterHub CILogonOAuthenticator for a hub are similar with the ones for enabling [GitHubOAuthenticator](auth:github-orgs):

### Create a CILogon OAuth client
This can be achieved by using the `deployer cilogon-client-create` command.

The command needs to be passed the cluster and hub name for which a client id and secret will be generated, but also the hub type, and the hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud).

Example script invocation that creates a CILogon OAuth client for the 2i2c dask-staging hub:

```bash
deployer cilogon-client-create 2i2c dask-staging daskhub dask-staging.2i2c.cloud
```

````{note}
If successful, the script will have created a secret values file under `config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml`. This file
holds the encrypted OAuth client id and secret that have been created for this hub.

The unencrypted file contents should look like this:
```yaml
  jupyterhub:
    hub:
      config:
        CILogonOAuthenticator:
          client_id: CLIENT_ID
          client_secret: CLIENT_SECRET
```
````

### Add the secret hub config file created in the step above to the list of helm chart values file
If not already present, add the secret hub config file to the list of helm chart values file in `config/clusters/<cluster_name>/cluster.yaml`. For example, if you created the `enc-<hub_name>.secret.values.yaml` file in the step above, add it to the `cluster.yaml` file like so:

```yaml
...
hubs:
  - name: <hub_name>
    ...
    helm_chart_values_files:
      - <hub_name>.values.yaml
      - enc-<hub_name>.secret.values.yaml
  ...
```

### Configure the authenticator

Edit the `config/clusters/<cluster_name>/<hub_name>.values.yaml` file to setup the authentication.

The most common CILogon configuration across 2i2c hubs is to allow users to authenticate using their own community institutional identity provider and 2i2c staff using Google.

For more complex configurations checkout the sections below and the (oauthenticator.cilogon docs](https://oauthenticator.readthedocs.io/en/latest/reference/api/gen/oauthenticator.cilogon.html).

```{important}
To get the value of the key that must go in the `allowed_idp` dict for a specific IdP, go to https://cilogon.org/idplist and get the value of the `EntityID` key of the desired institutional IdP.
```

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: cilogon
      Authenticator:
        admin_users:
          - admin@anu.edu.au
      CILogonOAuthenticator:
        oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
        # Show only the option to login with Google and ANU's provider
        shown_idps:
          - http://google.com/accounts/o8/id
          - https://idp2.anu.edu.au/idp/shibboleth
        # Allow to only login into the hub using Google or ANU's provider
        allowed_idps:
          http://google.com/accounts/o8/id:
            username_derivation:
              # Use the email as the hub username
              username_claim: "email"
            # Allow only 2i2c.org accounts to login through Google
            allowed_domains:
              - "2i2c.org"
          https://idp2.anu.edu.au/idp/shibboleth:
            username_derivation:
              # Use the email as the hub username
              username_claim: "email"
```

## Important rules to follow when using this method of authentication

1. The `admin_users` list need to match `allowed_idps` rules too.

2. It is recommended to define in the `allowed_idps` dict, all the identity providers we plan to allow to be used for a hub. This way, only these will be allowed to be used.

  ```{note}
  The keys allowed in the `allowed_idps` dict **must be valid CILogon `EntityIDs`**.
  Go to https://cilogon.org/idplist for the list of EntityIDs of each IdP.
  ```

3. All the identity providers must define a `username_derivation` scheme, with their own `username_claim`, that the user *cannot change*. If they can, it can be easily used to impersonate others! For example, if we allow both GitHub and `utoronto.ca` as allowed authentication providers, and only use `email` as `username_claim`, for both providers, any GitHub user can set their email field in their GitHub profile to a `utoronto.ca` email and thus gain access to any `utoronto.ca` user's server! So a very careful choice needs to
be made here.

  ```{note}
  You can check the [CILogon scopes section](https://www.cilogon.org/oidc#h.p_PEQXL8QUjsQm) to checkout available values for `username_claim`. This *cannot* be changed afterwards without manual migration of user names, so choose this carefully.
  ```

## Other CILogon common configurations across 2i2c clusters

### Authenticate using GitHub with CILogon**

*This example sets the GitHub nickname as the Hub username using the `username_claim` option*

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: cilogon
      CILogonOAuthenticator:
        scope:
          - "profile"
        oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
        shown_idps:
          - http://github.com/login/oauth/authorize
        allowed_idps:
          http://github.com/login/oauth/authorize:
            username_derivation:
              username_claim: "preferred_username"
```

```{important}
To learn about all the possible config options of the `CILogonOAuthenticator` dict, checkout [the docs](https://oauthenticator.readthedocs.io/en/latest/api/gen/oauthenticator.cilogon.html#oauthenticator.cilogon.CILogonOAuthenticator.allowed_idps).
```

## Switch Identity Providers or user accounts

By default, logging in with a particular user account will persist your credentials in future sessions.
This means that you'll automatically re-use the same institutional and user account when you access the hub's home page.

### Switch Identity Providers

1. **Logout of the Hub** using the logout button or by going to `https://{hub-name}/hub/logout`.
2. **Clear browser cookies** (optional). If the user asked CILogon to re-use the same Identity Provider connection when they logged in, they'll need to [clear browser cookies](https://www.lifewire.com/how-to-delete-cookies-2617981) for <https://cilogon.org>.

   ```{figure} ../../images/cilogon-remember-this-selection.png
   The dialog box that allows you to re-use the same Identity Provider.
   ```

   Firefox example:
   ```{figure} ../../images/cilogon-clear-cookies.png
   An example of clearing cookies with Firefox.
   ```

3. The next time the user goes to the hub's landing page, they'll be asked to re-authenticate and will be presented with the list of available Identity Providers after choosing the CILogon connection.
4. They can now choose **another Identity Provider** via CILogon.

```{note}
If the user choses the same Identity Provider, then they will be automatically logged in with the same user account they've used before. To change the user account, see [](auth:cilogon:switch-user-accounts).
```

(auth:cilogon:switch-user-accounts)=
### Switch user account

1. Logout of the Hub using the logout button or by going to `https://{hub-name}/hub/logout`.
2. Logout of CILogon by going to the [CILogon logout page](https://cilogon.org/logout).
3. The next time the user goes to the hub's landing page, they'll be asked to re-authenticate and will be presented with the list of available Identity Providers after choosing the CILogon connection.
4. Choose the **same Identity Provider** to login.
5. The user can now choose **another user account** to login with.

### 403 - Unauthorized errors

If you see a 403 error page, this means that the account you were using to login hasn't been allowed by the hub administrator.

```{figure} ../../images/403-forbidden.png
```

If you think this is an error, and the account should have been allowed, then contact the hub adminstrator/s.

If you used the wrong user account, you can log in using another account by following the steps in [](auth:cilogon:switch-user-accounts).
