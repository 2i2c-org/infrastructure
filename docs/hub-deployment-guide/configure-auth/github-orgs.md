(auth:github-orgs)=
# GitHub Orgs and Teams

For communities that require authenticating users against [a GitHub organisation or team](https://docs.github.com/en/organizations), we instead use the [native JupyterHub OAuthenticator](https://github.com/jupyterhub/oauthenticator).

## Get admin access to the target organisation

To more easily facilitate setting up this method of authentication, the engineer responsible for deploying the hub should have admin access to the organisation the Community Representative(s) want to use to manage its members.
We ask for this permission because, if the Community Representative doesn't grant permissions to the OAuth app during the first login, _all_ subsequent users will be see a `403 Forbidden` error when they try to login and correcting this can involve a lot of back-and-forth between us and the Community Representative.
This process is a lot more streamlined if we have the power to set this up ourselves.

Please ask the Community Representative on the "New Hub" issue to grant you admin access to the org before setting up this infrastructure.
You can remove yourself from the org once you have confirmed that login is working as expected.

## How-to setup GitHub auth

1. **Create a GitHub OAuth App.**
   This can be achieved by following [GitHub's documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app).
   - Create [a new app](https://github.com/organizations/2i2c-org/settings/applications/new) inside the
     `2i2c-org`.
   - When naming the application, please follow the convention `<cluster_name>-<hub_name>` for consistency, e.g. `2i2c-staging` is the OAuth app for the staging hub running on the 2i2c cluster.
   - The Homepage URL should match that in the `domain` field of the appropriate `cluster.yaml` file in the `infrastructure` repo.
   - The authorisation callback URL is the homepage url appended with `/hub/oauth_callback`. For example, `staging.pilot.2i2c.cloud/hub/oauth_callback`.
   - Once you have created the OAuth app, make a new of the client ID, generate a client secret and then hold on to these values for a future step

2. **Create or update the appropriate secret config file under `config/clusters/<cluster_name>/<hub_name>.secret.values.yaml`.**
   You should add the following config to this file, pasting in the client ID and secret you generated in step 1.

    ```yaml
    jupyterhub:
      hub:
        config:
          GitHubOAuthenticator:
            client_id: CLIENT_ID
            client_secret: CLIENT_SECRET
    ```

    ````{note}
    Add the `basehub` key above the `jupyterhub` key for `daskhub` deployments.
    For example:

    ```yaml
    basehub:
      jupyterhub:
        ...
    ```
    ````

    ```{note}
    Make sure this is encrypted with `sops` before committing it to the repository!

    `sops --output config/clusters/<cluster_name>/enc-<hub_name>.secret.values.yaml --encrypt config/clusters/<cluster_name>/<hub_name>.secret.values.yaml`
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

4. **Edit the non-secret config under `config/clusters/<cluster_name>/<hub_name>.values.yaml`,**
   making sure we ask for enough permissions (`read:org`) so we know what organizations (or
   teams) users are a part of

    ```yaml
    jupyterhub:
      custom:
        2i2c:
          add_staff_user_ids_to_admin_users: true
          add_staff_user_ids_of_type: github
      hub:
        config:
          JupyterHub:
            authenticator_class: github
          GitHubOAuthenticator:
            oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
            allowed_organizations:
              - ORG_NAME:TEAM_NAME
              - ORG_NAME
            scope:
              - read:org
    ```

    ````{note}
    Allowing access to a specific GitHub team, let's say `ORG_NAME:TEAM_NAME`, doesn't mean that the users that are only members of the TEAM_NAME sub-teams, e.g. `ORG_NAME:TEAM_NAME:SUB_TEAM_NAME`, will get access too.

    Instead, each sub-team must be explicitly added to the `allowed_organizations` list:
    ```yaml
    allowed_organizations:
        - ORG_NAME:TEAM_NAME
        - ORG_NAME:SUB_TEAM_NAME
    ```
    ````

5. Run the deployer as normal to apply the config.

### Granting access to the OAuth app

Once the OAuth callbacks have been set up following the steps above, you need to grant access to the OAuth app that we have created.

The first time that you log on to the hub with this authentication set up, you will be presented with a page that asks you to grant access to various GitHub organizations.
For each user, GitHub will list _all organizations of which they are a member_.

- Organisations with a green tick next to them already permit the app to read their data
- Organisations that you are a member of (but not an admin) have a "Request" button next to them.
  This will notify the org admins to grant access to this app on your behalf.
- Organisations that you are an admin of will have a "Grant" button next to them

If you have already logged in to the hub prior to adding the organization authentication you can perform the grant on the Authorized Oauth Apps tab of your accounts GitHub [Applications](https://github.com/settings/connections/applications/) Settings.

**You must grant access to the organization that is added to `allowed_organizations` in the config**, but do not need to grant access to any other organizations.
In this case, "granting access" only means that the JupyterHub can view whether a user is a member of the GitHub organization.

For example, see the image below for how we would grant the `nasa-cryo-staging` OAuth app access to the `binderhub-test-org`.

```{figure} ../../images/granting-org-access-to-oauth-app.jpg
How to grant org access to an OAuth app on GitHub
```

```{note}
If you need to reset the permissions of the app for any reason, see [](troubleshooting:reset-github-app).
You will **still** require admin access to the org to carry out those steps.
```

Once you have confirmed with the Community Representative that users can login, you can remove yourself from the org.

## Restricting user profiles based on GitHub Team Membership

JupyterHub has support for using [profileList](https://zero-to-jupyterhub.readthedocs.io/en/latest/jupyterhub/customizing/user-environment.html#using-multiple-profiles-to-let-users-select-their-environment)
to give users a choice of machine sizes and images to choose from when launching their
server.

In addition, we can allow people access to specific profiles based on their GitHub Teams membership!
This only works if the hub is already set to allow people only from certain GitHub organizations
to log in. See [](howto:features:profile-restrict) for more information.
### Enabling team based access on hub with pre-existing users

If this is being enabled for users on a hub with *pre-existing* users, they
will all need to be logged out before deployment. This would force them to
re-login next time, and that will set `auth_state` properly so we can filter
based on team membership - without that, we won't know which teams the user
belongs to, and they will get an opaque 'Access denied' error.

1. Check with the community to know *when* is a good time to log everyone
   out. If users have running servers, they will need to refresh the page -
   which will put them through the authentication flow again. It's best to
   do this at a time when minimal or no users are running, to minimize
   disruption.

2. We log everyone out by regenerating [hub.cookieSecret](https://z2jh.jupyter.org/en/stable/resources/reference.html#hub-cookiesecret).
   The easiest way to do this is to simply delete the kubernetes secret
   named `hub` in the namespace of the hub, and then do a deployment. So
   once the PR for deployment is ready, run the following command:

   ```bash
   # Get kubectl access to the cluster
   deployer use-cluster-credentials <cluster-name>
   kubectl -n <hub-name> delete secret hub
   ```

   After that, you can deploy either manually or by merging your PR.

This should log everyone out, and when they log in, they should see
the profiles they have access to!
