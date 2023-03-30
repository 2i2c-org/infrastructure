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
