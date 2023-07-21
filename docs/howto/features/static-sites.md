# Deploy authenticated static websites along the hub

```{warning}
This feature is currently broken. Tracked in [this issue](https://github.com/2i2c-org/infrastructure/issues/2206).
```

We can deploy *authenticated* static websites on the same domain as the hub
that is only accessible to users who have access to the hub. The source
for these come from git repositories that should contain rendered HTML,
and will be updated every 5 minutes. They can be under any prefix on the
same domain as the hub (such as `/docs`, `/textbook`, etc).

You can enable this with the following config in the `.values.yaml`
file for your hub.

```yaml

dex:
  # Enable authentication
  enabled: true
  hubHostName: <hostname-of-hub>

staticWebsite:
  enabled: true
  source:
    git:
      repo: <url-of-git-repo>
      branch: <name-of-git-branch>
  ingress:
    host: <hostname-of-hub>
    path: <absolute-path-where-content-is-available>

jupyterhub:
  hub:
    services:
      dex:
        url: http://dex:5556
        oauth_redirect_url: https://<hostname-of-hub>/services/dex/callback
        oauth_no_confirm: true
        display: false
      oauth2-proxy:
        display: false
        url: http://dex:9000

```

```{note}
We manually configure the hub services instead of autogenerating
them in our deploy scripts. This leads to some additional copy-pasting and
duplication, but keeps our config explicit and simple.
```

```{note}
`staticWebsite.ingress.path` should not have a trailing slash.
```

## Example

Here's a sample that hosts the data8 textbook under `https://staging.2i2c.cloud/textbook`:

```yaml
dex:
  enabled: true
  hubHostName: staging.2i2c.cloud

staticWebsite:
  enabled: true
  source:
    git:
      repo: https://github.com/inferentialthinking/inferentialthinking.github.io
      branch: master
  ingress:
    host: staging.2i2c.cloud
    path: /textbook

jupyterhub:
  hub:
    services:
      dex:
        url: http://dex:5556
        oauth_redirect_uri: https://staging.2i2c.cloud/services/dex/callback
        oauth_no_confirm: true
      oauth2-proxy:
        url: http://dex:9000
```

This clones the [repo]( https://github.com/inferentialthinking/inferentialthinking.github.io),
checks out the `master` branch and keeps it up to date by doing a
`git pull` every 5 minutes. It is made available under `/textbook`,
and requires users be logged-in to the hub before they can access it.

## Using private GitHub repos

We use [git-credentials-helper](https://github.com/yuvipanda/git-credential-helpers)
to support pulling content from private repos.

### Setup GitHub app

`git-credentials-helper` uses a [GitHub App](https://docs.github.com/en/developers/apps)
to pull private repos. So you first need to create a GitHub app for each hub that wants
to pull private repos as static content.

1. Create a [GitHub app in the 2i2c org](https://github.com/organizations/2i2c-org/settings/apps/new).

2. Give it a descriptive name (such as '<hub-name> static site deploy
   authenticator') and description, as users will see this when authorizing
   access to their private repos.

3. Disable webhooks (uncheck the 'Active' checkbox under 'Webhooks'). All other
   textboxes can be left empty.

4. Under 'Repository permissions', select 'Read' for 'Contents'.

5. Under 'Where can this GitHub App be installed?', select 'Any account'. This will
   enable users to push to their own user repositories or other organization repositories,
   rather than just the 2i2c repos.

6. Create the application with the 'Create GitHub app' button.

7. Copy the numeric 'App id' from the app info page you should be redirected to.

8. Create a new private key for authentication use with the `Generate a private key`
   button. This should download a private key file, that you should keep safe.

### Helm values configuration

Now, we can configure our static files server to make use of the GitHub app to authenticate.

1. Enable the gitHub app in the `.values.yaml` file for the hub.

   ```yaml
   staticWebsite:
     gitHubAuth:
       enabled: true
   ```

2. Create a sops-encrypted file (usually in the form of
   `enc-<hub-name>.secret.values.yaml`) to hold the secret values required to authenticate
   the GitHub app.

   ```yaml
   staticWebsite:
     githubAuth:
       githubApp:
         id: <id-of-the-app>
         privateKey: |
           <contents-of-private-key-file>
   ```

   Make sure this file is also listed under `helm_chart_values_files` for the hub in
   the cluster's `cluster.yaml` so it is read during deployment.

### Grant access to the private repo

Finally, someone with admin rights on the private repo to be pulled needs to
grant the github app we just setup access to the private repo. **This is the only
part that hub admins rather than 2i2c engineers need to do**.

1. Go to the 'Public page' of the GitHub app created. This usually is of the
   form `https://github.com/apps/<name-of-app>`. You can find this in the information
   page of the app after you create it, under 'Public link'

2. Install the app in the organization the private repo is in, and grant it access
   *only* to the repo that needs to be pulled.

### Do a deploy

After all the permissions are setup, you should make sure the config under
`staticWebsite.source.git.repo` and `staticWebsite.source.git.repo` are set appropriately, and do a deployment
to pull in the private repo!
