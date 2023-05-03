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

4. **Edit the non-secret config under `config/clusters/<cluster_name>/<hub_name>.values.yaml`.**
   You should make sure the matching hub config takes one of the following forms.

   ```{warning}
   When using this method of authentication, make sure to remove the `allowed_users` key from the config.
   This is because this key will block any user not listed under it **even if** they are valid members of the the organisation or team you are authenticating against.

   You should keep the `admin_users` key, however.
   ```

   To authenticate against a GitHub organisation (Note the `read:user` scope. See comment box below.):

    ```yaml
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

   To authenticate against a GitHub Team (Note the `read:org` scope. See the comment box below.):

    ```yaml
    jupyterhub:
      hub:
        config:
          JupyterHub:
            authenticator_class: github
          GitHubOAuthenticator:
            oauth_callback_url: https://{{ HUB_DOMAIN }}/hub/oauth_callback
            allowed_organizations:
              - 2i2c-org:hub-access-for-2i2c-staff
              - ORG_NAME:TEAM_NAME
            scope:
              - read:org
    ```

    ```{admonition} A note on scopes
    When authenticating against a whole organisation, we used the `read:user` scope in the example above.
    This means that the GitHub OAuth App will read the _user's_ profile to determine whether the currently authenticating user is a member of the listed organisation. **It also requires the user to have their membership of the organisation publicly listed otherwise authentication will fail, even if they are valid members.**

    To avoid this requirement, you may choose to use the `read:org` scope instead. This grants the GitHub OAuth App permission to read the profile of the _whole organisation_, however, and may be more powerful than the organisation owners wish to grant. So use your best judgment here.

    When authenticating against a GitHub Team, we are required to use the `read:org` scope as the GitHub OAuth App needs to know which teams belong to the organisation as well as the members of the specified team.
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
to log in.

The key `allowed_teams` can be set for any profile definition, with a list of GitHub
teams (formatted as `<github-org>:<team-name>`) or GitHub organizations (formatted
just as `<github-org>`) that will get access to that profile. Users
need to be a member of any one of the listed teams for access. The list of teams a user
is part of is fetched at login time - so if the user is added to a GitHub team, they need
to log out and log back in to the JupyterHub (not necessarily to GitHub!) to see the new
profiles they have access to. To remove access to a profile from a user, they have to be
removed from the appropriate team on GitHub *and* their JupyterHub user needs to be
deleted from the hub admin dashboard.

To enable this access,

1. Enable storing the list of GitHub teams a user is in as a part of
   [`auth_state`](https://zero-to-jupyterhub.readthedocs.io/en/latest/administrator/authentication.html#enable-auth-state)
   with the following config:

   ```yaml
   jupyterhub:
      hub:
        config:
          Authenticator:
            enable_auth_state: true
          GitHubOAuthenticator:
            populate_teams_in_auth_state: true
   ```

   If `populate_teams_in_auth_state` is not set, this entire feature is disabled.

2. Specify which teams or orgs should have access to which profiles with an
   `allowed_teams` key under `profileList`:

    ```yaml
    jupyterhub:
      singleuser:
        profileList:
          - display_name: "Small"
            description: 5GB RAM, 2 CPUs
            default: true
            allowed_teams:
              - <org-name>:<team-name>
              - 2i2c-org:hub-access-for-2i2c-staff
            kubespawner_override:
              mem_limit: 7G
              mem_guarantee: 4.5G
              node_selector:
                node.kubernetes.io/instance-type: n1-standard-2
          - display_name: Medium
            description: 11GB RAM, 4 CPUs
            allowed_teams:
              - <org-name>:<team-name>
              - 2i2c-org:hub-access-for-2i2c-staff
            kubespawner_override:
              mem_limit: 15G
              mem_guarantee: 11G
              node_selector:
                node.kubernetes.io/instance-type: n1-standard-4
    ```

    Users who are a part of *any* of the listed teams will be able to access that profile.
    Add `2i2c-org:teach-team` to all `allowed_teams` so 2i2c engineers can log in to debug
    issues. If `allowed_teams` is not set, that profile is not available to anyone.
