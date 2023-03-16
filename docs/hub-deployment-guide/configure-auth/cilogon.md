(auth:cilogon)=
# CILogon

[CILogon](https://www.cilogon.org) is a service provider that allows users to login against various identity providers, including campus identity providers. 2i2c can manage CILogon using the JupyterHub CILogonOAuthenticator.

Some key terms about CILogon authentication worth mentioning:

Identity Provider
: The authentication service available through the CILogon connection.

  When a user logs in via CILogon, they are first presented with a list of various institutions and organizations that they may choose from (e.g. `UC Berkeley` or `Australia National University`).

  The available identity providers are members of [InCommon](https://www.incommon.org/federation/), a federation of universities and other organizations that provide single sign-on access to various resources.

  Example:

  ```{figure} ../../images/cilogon-ipd-list.png
  A list of Identity Providers the user may select from.
  ```

User account
: Within an institution, each user is expected to have their own user account (e.g. `myname@berkeley.edu`). This is the account that is used to give somebody an ID on their JupyterHub. This is entered on an Identity Provider's login screen. For example:

  ```{figure} ../../images/cilogon-berkley-login-page.png
  The Berkeley authentication screen.
  ```

  ```{note}
  The JupyterHub usernames will be the **email address** that users provide when authenticating with an institutional identity provider. It will not be the CILogon `user_id`! This is because the `USERNAME_KEY` used for the CILogon login is the email address.
  ```

## JupyterHub CILogonOAuthenticator

The steps to enable the JupyterHub CILogonOAuthenticator for a hub are similar with the ones for enabling [GitHubOAuthenticator](auth:github-orgs):

1. **Create a CILogon OAuth client**
   This can be achieved by using the `deployer cilogon-client-create` command.

   - The command needs to be passed the cluster and hub name for which a client id and secret will be generated, but also the hub type, and the authorization callback URL.
   - The authorization callback URL is the homepage url appended with `/hub/oauth_callback`. For example, `https://staging.2i2c.cloud/hub/oauth_callback`.
   - Example script invocation that creates a CILogon OAuth client for the 2i2c dask-staging hub:
      ```bash
      deployer cilogon-client-create create 2i2c dask-staging daskhub https://dask-staging.2i2c.cloud/hub/oauth_callback
      ```
   - If successful, the script will have created a secret values file under `config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml`. This file
   holds the encrypted OAuth client id and secret that have been created for this hub.
   - The unencrypted file contents should look like this:
      ```yaml
        jupyterhub:
          hub:
            config:
              CILogonOAuthenticator:
                client_id: CLIENT_ID
                client_secret: CLIENT_SECRET
        ```

2. **Set the hub to _not_ configure Auth0 in the `config/clusters/<cluster_name>/cluster.yaml` file.**
   To ensure the deployer does not provision and configure an OAuth app from Auth0, the following config should be added to the appropriate hub in the cluster's `cluster.yaml` file.

   ```yaml
   hubs:
     - name: <hub_name>
       auth0:
         enabled: false
   ```

3. **If not already present, add the secret hub config file to the list of helm chart values file in `config/clusters<cluster_name>/cluster.yaml`.**
   If you created the `enc-<hub_name>.secret.values.yaml` file in step 2, add it the the `cluster.yaml` file like so:

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

4. **Edit the non-secret config under `config/clusters/<cluster_name>/<hub_name>.values.yaml`.**

   4.1. **A few rules of thumb when using this method of authentication:**

    - The `admin_users` list need to match `allowed_idps` rules too.

    - It is recommended to define in the `allowed_idps` dict, all the identity providers we plan to allow to be used for a hub. This way, only these will be allowed to be used.

      ```{note}
      The keys allowed in the `allowed_idps` dict **must be valid CILogon `EntityIDs`**.
      Go to https://cilogon.org/idplist for the list of EntityIDs of each IdP.
      ```

    - All the identity providers must define a `username_derivation` scheme, with their own `username_claim`, that the user *cannot change*. If they can, it can be easily used to impersonate others! For example, if we allow both GitHub and `utoronto.ca` as allowed authentication providers, and only use `email` as `username_claim`, for both providers, any GitHub user can set their email field in their GitHub profile to a `utoronto.ca` email and thus gain access to any `utoronto.ca` user's server! So a very careful choice needs to
    be made here.

      ```{note}
      You can check the [CILogon scopes section](https://www.cilogon.org/oidc#h.p_PEQXL8QUjsQm) to checkout available values for `username_claim`. This *cannot* be changed afterwards without manual migration of user names, so choose this carefully.
      ```

   4.2. **Most common configurations for 2i2c clusters:**

    1. **Only display specific identity provider as a login options**

        *This example uses GitHub as the only identity provider to show to the user.*

        ```yaml
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: cilogon
              CILogonOAuthenticator:
                # This config option will only display GitHub as the only identity provider option
                shown_idps:
                  - https://github.com/login/oauth/authorize
        ```

    2. **Authenticate using Google with CILogon, allowing only a certain domain**:

        *This example sets `2i2c.org` as the only domain that can login into the hub using Google*

        ```yaml
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: cilogon
              CILogonOAuthenticator:
                oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
                allowed_idps:
                  http://google.com/accounts/o8/id:
                    username_derivation:
                      username_claim: "email"
                    allowed_domains:
                        - "2i2c.org"
        ```

    3. **Authenticate using GitHub with CILogon**:

        *This example sets the GitHub nickname as the Hub username using the `username_claim` option*

        ```yaml
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: cilogon
              CILogonOAuthenticator:
                oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
                shown_idps:
                  - http://github.com/login/oauth/authorize
                allowed_idps:
                  http://github.com/login/oauth/authorize:
                    username_derivation:
                      username_claim: "preferred_username"
        ```

    4. **Authenticate using an institutional identity provider for the hub community users and Google for 2i2c staff.**

        This example:
          - only shows Shibboleth, the ANU identity provider, and Google as the possible login options through CILogon
          - sets `2i2c.org` as the only domain that can login to the hub using Google
          - sets `anu.edu.au` as the only domain that can login to the hub using Shibboleth
          - adds a `2i2c:` prefix to the usernames logging in through Google. The hub usernames are the `email` addresses of these accounts, as specified through `username_claim`.
          - strips the `@anu.edu.au` domain from the usernames logging in through Shibboleth. The hub usernames are the `email` addresses of these accounts, as specified through `username_claim`.

      ```{note}
      To get the value of the key that must go in the `allowed_idp` dict for a specific IdP, go to https://cilogon.org/idplist and get the value of the `EntityID` key of the desired institutional IdP.
      ```

      Example config:

      ```yaml
      jupyterhub:
        hub:
          config:
            JupyterHub:
              authenticator_class: cilogon
            CILogonOAuthenticator:
              oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
              admin_users:
                - admin@anu.edu.au
              # Only show the option to login with Google and Shibboleth
              shown_idps:
                - https://idp2.anu.edu.au/idp/shibboleth
                - http://google.com/accounts/o8/id
              allowed_idps:
                http://google.com/accounts/o8/id:
                  username_derivation:
                    username_claim: "email"
                    action: "prefix"
                    prefix: "2i2c"
                  allowed_domains:
                    - "2i2c.org"
                https://idp2.anu.edu.au/idp/shibboleth:
                  username_derivation:
                    username_claim: "email"
                    action: "strip_idp_domain",
                    domain: "anu.edu.au"
                  allowed_domains:
                    - "anu.edu.au"
      ```

   ```{note}
   To learn about all the possible config options of the `CILogonOAuthenticator` dict, checkout [the docs](https://oauthenticator.readthedocs.io/en/latest/api/gen/oauthenticator.cilogon.html#oauthenticator.cilogon.CILogonOAuthenticator.allowed_idps).
   ```

5. Run the deployer as normal to apply the config.


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
