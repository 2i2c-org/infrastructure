(auth:canvas)=

# Canvas

[Canvas](https://www.instructure.com/canvas/) is a commercial web-based learning management system (LMS) that some communities
already have access to at their affiliated institutions. It implements features like the Learning Tools Interoperability (LTI) standard,
and implements an OAuth2 provider. Consequently, some communities are interested in integrating their JupyterHubs with the existing
identity management and user management features provided by Canvas.

## Set up the hub with GenericOAuthenticator

As an OAuth2 provider, Canvas can quickly be integrated into a JupyterHub through the `GenericOAuthenticator` class. We can define most of the necessary configuration in the base Helm values for a particular hub. To begin, let's enable the `GenericOAuthenticator`:

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: generic-oauth
```

Next, we need to know the Canvas instance's URL. Usually this is of the form <https://some-institution.instructure.com>. We will use the `jupyterhub_oauthenticator_authz_helpers` package to facilitate the basic authentication process:

```{code-block} yaml
:emphasize-lines: 7-9, 11-
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: generic-oauth

    config:
      GenericOAuthenticator:
        username_claim: sis_user_id

    extraConfig:
      001-canvas-auth: |
        from jupyterhub_oauthenticator_authz_helpers.canvas import build_auth_urls
        canvas_url = "https://utoronto-dev.instructure.com"

        cfg = c.GenericOAuthenticator

        # Setup auth URLs
        cfg.authorize_url, cfg.token_url, cfg.userdata_url = build_auth_urls(canvas_url)

        # Scopes that the provisioned token will need, previously provided to the Canvas administrators
        cfg.scope = [*build_auth_urls.scopes]
```

When the Hub queries the `userdata_url` endpoint to resolve information about the granted token, it needs guidance on which field to consume as the username in the response. Details of the `User` object returned by this endpoint response can be found [on the Canvas API docs](https://developerdocs.instructure.com/services/canvas/resources/users). The Student Information System (SIS) that is integrated with Canvas records its user ID in the `sis_user_id` field.

Simultaneously, in the public per-hub config (of form `<hub-name>.secret.values.yaml`), we define the OAuth redirect URL for each hub:

```{code-block} yaml
:emphasize-lines: 5
jupyterhub:
  hub:
    config:
      GenericOAuthenticator:
        oauth_callback_url: https://<hub-domain>/hub/oauth_callback
```

Although this is mostly boilerplate at this stage, later additions for things like course-based access controls (authorization) are easy to slot in with this approach.

## Define the OAuth secrets

OAuth2 relies on the existence of a public `client_id` and a private `client_secret` in order for authentication of "confidential" applications like a JupyterHub. Out of an abundance of caution, we store both the secret and the client ID in encrypted storage. We must ask the community's Canvas administrators to provision us with these secrets in the form of a dev-key. Downstream, the JupyterHub authentication flow may only request scopes that were previously defined at the issuance of the dev-key, so we must also provide these to the community along with the necessary scopes. We must also provide the OAuth redirect URL, which is used to ensure that only our Hub is granted use of this application. In total:

```{note} Which scopes do I need?
At a minimum, we need the the `url:GET|/api/v1/users/:user_id/profile` scope that grants us permission to query the profile endpoint. This is used to derive the username from the provided token.
```

In the encrypted, per-hub config (of form `enc-<hub-name>.secret.values.yaml`), we specify the secret values we received from the community.

```{code-block} yaml
:emphasize-lines: 5-
jupyterhub:
  hub:
    config:
      GenericOAuthenticator:
        client_id: <client-id>
        client_secret: <client-secret>
        logout_redirect_url: https://<auth0-domain>/v2/logout?client_id=<client-id>

```
