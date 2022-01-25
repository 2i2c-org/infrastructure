# Manage authentication

## Auth0

[auth0](https://auth0.com) provides authentication for the majority of 2i2c hubs. It can
be configured with many different [connections](https://auth0.com/docs/identityproviders)
that users can authenticate with - such as Google, GitHub, etc.

So we want to manage authentication by:

1. Explicitly listing the type of connection we want for this hub, via
   `auth0.connection`. Currently common ones are `google-oauth2` for Google &
   `github` for GitHub. *Users* of the hub will use this method to log in to
   the hub.

   You can set the auth0 connector for a hub with:

   ```yaml
   auth0:
      connection: google-oauth2
   ```

   Theoretically, every provider in [this list](https://auth0.com/docs/connections/identity-providers-social)
   is supported. However, we've currently only tested this with Google
   (`google-oauth2`) and GitHub (`github`)

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
   config:
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

```{admonition} Switching auth
Switching authentication providers (e.g. from GitHub to Google) for a pre-existing hub will simply create new usernames. Any pre-existing users will no longer be able to access their accounts (although administrators will be able to do so). If you have pre-existing users and want to switch the hub authentication, rename the users to the new auth pattern (e.g. convert github handles to emails).
```

## Native JupyterHub OAuthenticator for GitHub Orgs and Teams

```{note}
This setup is currently only supported for communities that **require** authentication via a GitHub organisation or team.

We may update this policy in the future.
```

For communities that require authenticating users against [a GitHub organisation or team](https://docs.github.com/en/organizations), we instead use the [native JupyterHub OAuthenticator](https://github.com/jupyterhub/oauthenticator).
Presently, this involves a few more manual steps than the `auth0` setup described above.

1. **Create a GitHub OAuth App.**
   This can be achieved by following [GitHub's documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app).
   - Use the "Switch account" button at the top of your settings page to make sure you have `2i2c-org` selected.
     That way, the app will be owned by the `2i2c-org` GitHub org, rather than your personal GitHub account.
   - When naming the application, please follow the convention `<CLUSTER_NAME>-<HUB_NAME>` for consistency, e.g. `2i2c-staging` is the OAuth app for the staging hub running on the 2i2c cluster.
   - The Homepage URL should match that in the `domain` field of the appropriate `*.cluster.yaml` file in the `infrastructure` repo.
   - The authorisation callback URL is the homepage url appended with `/hub/oauth_callback`. For example, `staging.pilot.2i2c.cloud/hub/oauth_callback`.
   - Once you have created the OAuth app, make a new of the client ID, generate a client secret and then hold on to these values for a future step

2. **Create or update the appropriate secret config file under `secrets/config/hubs/*.cluster.yaml`.**
   You should add the following config to this file, pasting in the client ID and secret you generated in step 1.

    ```yaml
    hubs:
    - name: HUB_NAME
      config:
        jupyterhub:
          hub:
            config:
              GitHubOAuthenticator:
                client_id: CLIENT_ID
                client_secret: CLIENT_SECRET
    ```

    ````{note}
    Add the `basehub` key between `config` and `jupyterhub` for `daskhub` deployments.
    For example:

    ```yaml
    hubs:
    - name: HUB_NAME
      config:
        basehub:
          jupyterhub:
            ...
    ```
    ````

    ```{note}
    Make sure this is encrypted with `sops` before committing it to the repository!

    `sops -i -e secrets/config/hubs/*.cluster.yaml`
    ```

3. **Edit the non-secret config under `config/hubs`.**
   You should make sure the matching hub config takes one of the following forms.

   ```{admonition} Removing allowed users
   When using this method of authentication, make sure to remove the `allowed_users` block from the config.
   This is because this block will block any user not listed under it **even if** they are valid members of the the organisation or team you are authenticating against.

   You should keep the `admin_users` block, however.
   ```

   To authenticate against a GitHub organisation:

    ```yaml
    hubs:
    - name: HUB_NAME
      auth0:
        enabled: false
      ... # Other config
      config:
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: github
              GitHubOAuthenticator:
                oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
                allowed_organizations:
                  - 2i2c-org
                  - ORG_NAME
                scope:
                  - read:user
    ```

   To authenticate against a GitHub Team:

    ```yaml
    hubs:
    - name: HUB_NAME
      auth0:
        enabled: false
      ... # Other config
      config:
        jupyterhub:
          hub:
            config:
              JupyterHub:
                authenticator_class: github
              GitHubOAuthenticator:
                oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
                allowed_organizations:
                  - 2i2c-org:tech-team
                  - ORG_NAME:TEAM_NAME
                scope:
                  - read:org
    ```

4. Run the deployer as normal to apply the config.

## CILogon

[CILogon](https://www.cilogon.org) allows us to authenticate users against their campus identity providers. It is managed through [auth0](https://auth0.com), similar to Google and GitHub authentication.

```{seealso}
See the [CILogon documentation on `Auth0`](https://www.cilogon.org/auth0) for more configuration information.
```
```{note}
The JupyterHub username will be the email address that users provide when authenticating in CILogon connection. It will not be the CILogon `user_id`! This is because the `USERNAME_KEY` used for the CILogon login is the email address.
```

To enable CILogon authentication:

1. Explicitly list CILogon as the type of connection we want for a hub, via `auth0.connection`:

   ```yaml
   auth0:
      connection: CILogon
   ```

2. Explicitly list *admin users* for a given hub and only allow the users that match specific identity providers to login into the hub.

  ```{note}
  Don't forget to allow login to the test user (`deployment-service-check`), otherwise the hub health check performed during deployment will fail.
  ```

  ```yaml
    config:
      jupyterhub:
        hub:
          config:
            Authenticator:
              admin_users:
                - user1@campus.edu
                - user2@gmail.com
                # This will be replaced with the staff's google addresses
                - <staff_google_ids>
              username_pattern: '^(.+@2i2c\.org|.+@campus\.edu|deployment-service-check)$'
   ```

  This example does two things:

  1. Sets the hub admins to be:

    - the 2i2c staff (identified through their 2i2c email address)
    - one `@campus.edu` user
    - one `@gmail.com` user

  2. Allows logging in only the users that match the `username_pattern` expression:

    - all `@2i2c.org` email adresses
    - all `@campus.edu` email addresses
    - `user2@gmail.com`
    - the test username, `deployment-service-check`

  ```{note}
  All the users listed under `admin_users` need to match the `username_pattern` expression otherwise they won't be allowed to login!
  ```