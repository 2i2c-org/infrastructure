# Auth0

[`auth0`](https://auth0.com) provides authentication for the majority of 2i2c hubs. It can
be configured with many different [connections](https://auth0.com/docs/identityproviders)
that users can authenticate with - such as Google, GitHub, etc.

:::{note}
If you wish to authenticate users based on their membership in a GitHub organization or team, you'll need to use [the native GitHub OAuthenticator instead](auth:github-orgs).
:::

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
