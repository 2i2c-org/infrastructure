(auth:auth0)=
# Auth0

[Auth0](https://auth0.com/) is a commercial authentication provider that some communities
would like to use, for the various extra features it offers. Since it's outside the primary
two authentication mechanisms we offer, this costs extra - please confirm with partnerships
team that the community is being billed for it.

## Set up the hub with CILogon

First, we set up the hub and use [CILogon](auth:cilogon) for authentication, so the community
can get started and poke around. This decouples getting started from the auth0 process,
to make everything smoother (for both 2i2c engineers and the community).

## Requesting credentials from the community

We have to ask the community to create and provision Auth0 credentials for us. They will need
to create a [Regular Auth0 Web App](https://auth0.com/docs/get-started/auth0-overview/create-applications/regular-web-apps)
for each hub - so at the least, for the staging hub and the production hub.

Under [Application URIs](https://auth0.com/docs/get-started/applications/application-settings#application-uris),
they should use the following URL under "Allowed Callback URLs":

`https://<domain-of-the-hub>/hub/oauth_callback`

Once created, they should collect the following information:

1. `client_secret` and `client_id` for the created application.
2. The "Auth0 domain" for the created application.

These are *secure credentials*, and must be sent to us using [the encrypted support mechanism](https://docs.2i2c.org/support/#send-us-encrypted-content)

They can configure this with whatever [connections](https://auth0.com/docs/connections) they
prefer - 2i2c is not responsible for and hence can not really help with configuring this.

```{note}

It may be advantageous to 2i2c engineers to have shared access to this auth0 web application,
so we can debug issues that may arise. But we don't want to create too much friction here,
by having to manually create accounts for each 2i2c engineer for each auth0 application we
administer. Solutions (potentially a shared account) are being explored.
```

## Configuring the JupyterHub to use Auth0

While there is an upstream [Auth0OAuthenticator](https://github.com/jupyterhub/oauthenticator/blob/main/oauthenticator/auth0.py),
it doesn't have any specific features that aren't in the upstream [GenericOAuthenticator](https://oauthenticator.readthedocs.io/en/latest/reference/api/gen/oauthenticator.generic.html),
and is missing some features that are present in the GenericOAuthenticator. Using the GenericOAuthenticator
here also allows us to support other Generic OAuth providers in the future, and not tie ourselves down
to Auth0.

In the `common.yaml` file for the cluster hosting the hubs, we set the authenticator to be `generic`.

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: generic
```

In the encrypted, per-hub config (of form `enc-<hub-name>.secret.values.yaml`), we specify the secret values
we received from the community.

```yaml
jupyterhub:
  hub:
    config:
      GenericOAuthenticator:
        client_id: <client-id>
        client_secret: <client-secret>
        logout_redirect_url: https://<auth0-domain>/v2/logout?client_id=<client-id>
```

And in the *unencrypted*, per-hub config (of form `<hub-name>.values.yaml`), we specify the non-secret
config values.

```yaml
jupyterhub:
  hub:
    config:
      GenericOAuthenticator:
        token_url: https://<auth0-domain>/oauth/token
        authorize_url: https://<auth0-domain>/authorize
        userdata_url: https://<auth0-domain>/userinfo
        scope: openid
        username_claim: sub
```

Auth0 has documentation for the [userinfo](https://auth0.com/docs/api/authentication#get-user-info),
[token](https://auth0.com/docs/api/authentication#authenticate-user) and [authorize](https://auth0.com/docs/api/authentication#social)
endpoints.

Once deployed, this should allow users authorized by Auth0 to login to the hub! Their usernames will
look like `<auth-provider>:<id>`, which looks a little strange but allows differentiation between
people who use multiple accounts but the same email.