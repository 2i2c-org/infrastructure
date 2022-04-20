# Allow users to push to GitHub

We use [gh-scoped-creds](https://github.com/yuvipanda/gh-scoped-creds/) to
allow users to safely push to GitHub from their JupyterHub. This requires
a little setup on the hub side to make the user experience seamless.

1. [Create a GitHub app](https://github.com/organizations/2i2c-org/settings/apps/new)
   under the 2i2c organization with the settings
   [outlined in the gh-scoped-creds docs](https://github.com/yuvipanda/gh-scoped-creds/#github-app-configuration)

2. Set [environment variables](https://github.com/yuvipanda/gh-scoped-creds/#client-configuration)
   `gh-scoped-creds` needs to figure out which GitHub app to use in the appropriate
   `.values.yaml` file for the hub in question.

   ```yaml
    jupyterhub:
      singleuser:
         extraEnv:
            GH_SCOPED_CREDS_CLIENT_ID: <client-id-of-the-github-app>
            GH_SCOPED_CREDS_APP_URL: <public-url-of-the-github-app>
   ```

   ```{note}
   If the hub is a `daskhub`, nest the config under a `basehub` key
   ```

   Get this change deployed!

3. Make sure the [gh-scoped-creds](https://pypi.org/project/gh-scoped-creds/) python
   package is available inside the user image.

[This blog post](https://blog.jupyter.org/securely-pushing-to-github-from-a-jupyterhub-3ee42dfdc54f)
provides more details on how users on the JupyterHub can use `gh-scoped-creds` to
push changes to GitHub!