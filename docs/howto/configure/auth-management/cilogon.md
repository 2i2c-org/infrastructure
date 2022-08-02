# CILogon

[CILogon](https://www.cilogon.org) is a service provider that allows users to login against various identity providers, including campus identity providers. 2i2c can manage CILogon either using the JupyterHub CILogonOAuthenticator or through [auth0](https://auth0.com), similar to Google and GitHub authentication.

Some key terms about CILogon authentication worth mentioning:

Identity Provider
: The authentication service available through the CILogon connection.

  When a user logs in via CILogon, they are first presented with a list of various institutions and organizations that they may choose from (e.g. `UC Berkeley` or `Australia National University`).

  The available identity providers are members of [InCommon](https://www.incommon.org/federation/), a federation of universities and other organizations that provide single sign-on access to various resources.

  Example:

  ```{figure} ../../../images/cilogon-ipd-list.png
  A list of Identity Providers the user may select from.
  ```

User account
: Within an institution, each user is expected to have their own user account (e.g. `myname@berkeley.edu`). This is the account that is used to give somebody an ID on their JupyterHub. This is entered on an Identity Provider's login screen. For example:

  ```{figure} ../../../images/cilogon-berkley-login-page.png
  The Berkeley authentication screen.
  ```

  ```{note}
  The JupyterHub usernames will be the **email address** that users provide when authenticating with an institutional identity provider. It will not be the CILogon `user_id`! This is because the `USERNAME_KEY` used for the CILogon login is the email address.
  ```

## JupyterHub CILogonOAuthenticator

The steps to enable the JupyterHub CILogonOAuthenticator for a hub are simmilar with the ones for enabling [GitHubOAuthenticator](auth:github-orgs):

1. **Create a CILogon OAuth client**
   This can be achieved by using the [cilogon_app.py](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/cilogon_app.py) script.

   - The script needs to be passed the cluster and hub name for which a client id and secret will be generated, but also the hub type, and the authorisation callback URL.
   - The authorisation callback URL is the homepage url appended with `/hub/oauth_callback`. For example, `staging.pilot.2i2c.cloud/hub/oauth_callback`.
   - Example script invocation that creates a CILogon OAuth client for the 2i2c dask-staging hub:
      ```bash
      python3 ./deployer/cilogon_app.py create 2i2c dask-staging daskhub https://dask-staging.2i2c.cloud/hub/oauth_callback
      ```
   - If successfull, the script will have created a secret values file under `config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml`. This file
   holds the encrypted OAuth client id and secret that have been created for this hub.
   - The unecrypted file contents should look like this:
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

5. **Edit the non-secret config under `config/clusters/<cluster_name>/<hub_name>.values.yaml`.**
   You should make sure the matching hub config takes one of the following forms.

   ```{warning}
   When using this method of authentication, make sure to remove the `allowed_users` key from the config.
   This is because this key will block any user not listed under it **even if** they are valid members of the the organisation or team you are authenticating against.

   Also, the `admin_users` list need to match `allowed_idps` currently.
   Reference https://github.com/jupyterhub/oauthenticator/issues/494.
   ```

   To authenticate using CILogon, allowing only a certain identity provider:

    ```yaml
    jupyterhub:
      hub:
        config:
          JupyterHub:
            authenticator_class: cilogon
          CILogonOAuthenticator:
            oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
            username_claim: USERNAME_KEY
            allowed_idps:
              - 2i2c.org
              - IDP
    ```

  Check the [CILogon scopes
  section](https://www.cilogon.org/oidc#h.p_PEQXL8QUjsQm) to checkout available
  values for `USERNAME_KEY` claim. This *cannot* be changed afterwards without manual
  migration of user names, so choose this carefully.

  ```{warning}
  `USERNAME_KEY` should be something the user *cannot change* in any of the identity providers
  we support. If they can, it can be easily used to impersonate others! For example, if we allow
  both GitHub and `utoronto.ca` as allowed authentication providers, and only use `email` as
  `USERNAME_KEY`, any GitHub user can set their email field in their GitHub profile to a `utoronto.ca`
  email and thus gain access to any `utoronto.ca` user's server! So a very careful choice needs to
  be made here.
  ```

6. Run the deployer as normal to apply the config.

## CILogon through Auth0

```{seealso}
See the [CILogon documentation on `Auth0`](https://www.cilogon.org/auth0) for more configuration information.
```

The steps to enable the CILogon authentication through Auth0 for a hub are:

1. List CILogon as the type of connection we want for a hub, via `auth0.connection` in the `cluster.yaml` file:

   ```yaml
   auth0:
      connection: CILogon
   ```

2. Add **admin users** to the hub by explicitly listing their email addresses. Add **allowed users** for the hub by providing a regex pattern that will match to an institutional email address. (see example below)

  ```{note}
  Don't forget to allow login to the test user (`deployment-service-check`), otherwise the hub health check performed during deployment will fail.
  ```

### Example config for CILogon through Auth0

The CILogon connection works by providing users the option to login into a hub using any CILogon Identity Provider of their choice, as long as the email address of the user or the entire organization (e.g. `*@berkeley.edu`) has been provided access into the hub.

The following configuration example shows off how to configure hub admins and allowed users:

1. **Hub admins** are these explicit emails:
   - one `@campus.edu` user
   - one `@gmail.com` user
   - the 2i2c staff (identified through their 2i2c email address)

2. **Allowed users** are matched against a pattern, with a few specific addresses added in as well
   - all `@2i2c.org` email adresses
   - all `@campus.edu` email addresses
   - `user2@gmail.com`
   - the test username, `deployment-service-check`

```yaml
jupyterhub:
  custom:
    2i2c:
      add_staff_user_ids_to_admin_users: true
      add_staff_user_ids_of_type: "google"
  hub:
    config:
      Authenticator:
        admin_users:
          - user1@campus.edu
          - user2@gmail.com
        username_pattern: '^(.+@2i2c\.org|.+@campus\.edu|user2@gmail\.com|deployment-service-check)$'
```

```{note}
All the users listed under `admin_users` need to match the `username_pattern` expression otherwise they won't be allowed to login!
```

## Switch Identity Providers or user accounts

By default, logging in with a particular user account will persist your credentials in future sessions.
This means that you'll automatically re-use the same institutional and user account when you access the hub's home page.

### Switch Identity Providers

1. **Logout of the Hub** using the logout button or by going to `https://{hub-name}/hub/logout`.
2. **Clear browser cookies** (optional). If the user asked CILogon to re-use the same Identity Provider connection when they logged in, they'll need to [clear browser cookies](https://www.lifewire.com/how-to-delete-cookies-2617981) for <https://cilogon.org>.

   ```{figure} ../../../images/cilogon-remember-this-selection.png
   The dialog box that allows you to re-use the same Identity Provider.
   ```

   Firefox example:
   ```{figure} ../../../images/cilogon-clear-cookies.png
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

```{figure} ../../../images/403-forbidden.png
```

If you think this is an error, and the account should have been allowed, then contact the hub adminstrator/s.

If you used the wrong user account, you can log in using another account by following the steps in [](auth:cilogon:switch-user-accounts).
