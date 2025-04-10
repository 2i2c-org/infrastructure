# Integrate community-documentation with Jupyter Book

With [`#5045`][mvp], we now support the ability to connect community-documentation with a deployed Hub. From an infrastructure perspective, this is a thin integration in which we deliver the following features:

- A hub-adjacent public subdomain `docs.<COMMUNITY>.2i2c.cloud`
- Default Jupyter Book configuration to use our Binder/JupyterHub

## Create a custom subdomain for the book

We currently use Namecheap to manage the domains of our hubs. A `CNAME` record for the `docs` subdomain should be added alongside the hub's existing records, and point to the deployed Jupyter Book static site.

:::{note}
For the current iteration of this feature, we expect that users will deploy their static sites to GitHub Pages under their own organisation. Therefore, we will need the users to provide us with the URL of their deployed documentation.
:::

## Configure the book to use the hub

### Hubs that deploy a BinderHub

If the hub is deployed alongside a BinderHub, its URL can be added to the [`myst.yml`][frontmatter] `binder` property. This will enable the per-page launch-button that allows users to jump into an execution context with a JupyterHub or BinderHub. Setting the `binder` field will also set the default BinderHub URL to the given URL.

### Hubs without a BinderHub

For hubs that do not deploy a BinderHub, the launch-button UI can be enabled by setting the default [`myst.yml`][frontmatter] `binder` property to <https://mybinder.org>. As described above, this will enable the launch-button UI.

[mvp]: https://github.com/2i2c-org/infrastructure/issues/5045
[frontmatter]: https://mystmd.org/guide/frontmatter#available-frontmatter-fields
