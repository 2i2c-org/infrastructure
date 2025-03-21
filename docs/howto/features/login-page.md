# Configure the hub login page

Each Hub deployed in a cluster has a collection of metadata about who it is deployed for, and who is responsible for running it. This is used to generate the **log-in page** for each hub and tailor it for the community.

For an example, see [the log-in page of the staging hub](https://staging.2i2c.cloud/hub/login).

The log-in pages are built with [the base template at this repository](https://github.com/2i2c-org/default-hub-homepage). Values are inserted into each template based on each hub configuration.
By default, the main branch of this repository will be used for customization. But both the repository and the branch can be configured for each hub.

You may customize the configuration for a hub's homepage `jupyterhub.homepage.templateVars` in the appropriate hub values file under `config/clusters/<cluster_name>`. Changing these values for a hub will ensure that the hub's landing page updates automatically.
Some example config is below.

```yaml
jupyterhub:
  custom:
    homepage:
      gitRepoBranch: "<cluster-name>-<hub-name>"
      gitRepoUrl: "https://github.com/some-org/some-repo"
      templateVars:
        org:
          name: Org Name
          url: https://some-site.org
          logo_url: https://some-site.org/media/logo.png
        designed_by:
          name: 2i2c
          url: https://2i2c.org
        operated_by:
          name: 2i2c
          url: https://2i2c.org
        funded_by:
          name: Some Funder
          url: https://some-funding.org
```

## Redirect the logged out page to a different URL

Sometimes communities want to maintain their own landing page in their own content management
systems, consistent with their styling and practices. We can redirect the default logged out
home page (what users see when they go to the hub but haven't logged in) to any such URL easily.

Use the following config:

```yaml
jupyterhub:
  custom:
    homepage:
      templateVars:
        redirect_to: <full URL to redirect to>
```

If you specify a `redirect_to` URL, you can't specify the other parameters mentioned earlier.

The page maintained by the community should contain a "Login" link that points to an appropriately
constructed URL. The following are some common URL constructions:

1. `https://<domain-of-the-hub>/hub/oauth_login` will ask the user to log in if
   necessary, and send them to the default configured experience for the hub (such
   as a profile list, JupyterLab, or RStudio). This is the most common URL to use.
2. `https://<domain-of-the-hub>/hub/user-redirect/lab` is valid only on hubs that don't
   offer the user a profile list to choose from, and will send them to JupyterLab after
   logging in. Alternatively, you can use `https://<domain-of-the-hub>/hub/user-redirect/rstudio`
   to send them to RStudio (if it's installed in your image) after login,
   `https://<domain-of-the-hub>/hub/user-redirect/tree` for classic Jupyter Notebook,
   or `https://<domain-of-the-hub>/hub/user-redirect/desktop` for Linux Desktop (if available in
   your image)
3. A link generated with the [nbgitpuller Link Generator](https://nbgitpuller.readthedocs.io/en/latest/link.html)
   may also be used if you want to send the user to a particular repository pulled in by nbgitpuller.

### Staging Hub Considerations

We would like staging hubs to have the same configuration as production hubs to the extent possible.
So if you're redirecting your production hub's home page, you should redirect the staging hub's as well.
There are two ways to approach this:

1. Redirect the staging and production hubs to the same community page. This works fine, but makes it *really*
   confusing to log in to the staging hub to test anything, as the login link in the community maintained page is
   probably pointing to the *production* hub! Anyone wanting to login to the staging hub will have to use a manually
   constructed link (via formats specified above).

2. Ask the community to maintain two different pages - one for staging and one for production. And redirect each
   hub appropriately.

Option (2) is preferred to minimize confusion.