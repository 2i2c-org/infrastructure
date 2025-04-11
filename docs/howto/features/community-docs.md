# Integrate community-documentation with Jupyter Book

With [`#5045`][mvp], we now support the ability to connect community-documentation with a deployed Hub. From an infrastructure perspective, this is a thin integration in which we deliver the following features:

- A GitHub repository template for community documentation.
- A hub-adjacent public subdomain `docs.<COMMUNITY>.2i2c.cloud`.
- Default Jupyter Book configuration to use our Binder/JupyterHub.

## Create the community documentation repo

There is a template repository for the community docs at [2i2c-org/community-docs-template]. The community representative should [use this template to create their own repo][use-template], and provide us with _temporary_ owner access.

We must then enable [GitHub Pages deployment via GitHub Actions][pages] for the repo, which will then deploy to `https://<ORG>.github.io/<REPO>/`.

## Use a custom subdomain for the book

We currently use [Namecheap] to manage the domains of our hubs. A [CNAME] record for the `docs` subdomain (e.g. `docs.<COMMUNITY>.2i2c.cloud`) should be added alongside the hub's existing records, and point to the deployed Jupyter Book static site, e.g. `<ORG>.github.io`.

Once the CNAME record has been established, the repo must be [configured to use a custom domain][repo-domain], e.g. `docs.<COMMUNITY>.2i2c.cloud`.

:::{admonition} What about `BASE_URL`?
:class: dropdown note

The [2i2c-org/community-docs-template] pre-configures the `BASE_URL` environment variable to reflect a custom-domain deployment. This means that initial GitHub Pages deployment to `https://<ORG>.github.io/<REPO>` will not render properly. This is expected; the site deployed on the custom domain will render properly.
:::

## Add Binder/JupyterHub configuration to the book

### Hubs that deploy a BinderHub

If the hub is deployed alongside a BinderHub, its URL can be added to the [`myst.yml`'s `project.binder` property][frontmatter], e.g.

```{code-block} yaml
:emphasize-lines: 11
:linenos:

# See docs at: https://mystmd.org/guide/frontmatter
version: 1
project:
  id: df8b4a16-be6c-4b92-abcc-a95e23b9684a
  # title:
  # description:
  # keywords: []
  # authors: []
  github: https://github.com/2i2c-org/community-docs-template
  # To autogenerate a Table of Contents, run "jupyter-book init --write-toc"
  binder: https://binder.<COMMUNITY>.2i2c.cloud/
  toc:
    - file: content/index.md
    - file: content/kb/index.md
    - file: content/metrics.md
```

This will enable the per-page launch-button that allows users to jump into an execution context with a JupyterHub or BinderHub. Setting the `binder` field will also set the default BinderHub URL to the given URL.

### Hubs without a BinderHub

For hubs that do not deploy a BinderHub, the launch-button UI can be enabled by setting the default [`myst.yml`'s `project.binder` property][frontmatter] to <https://mybinder.org>, e.g.

```{code-block} yaml
:emphasize-lines: 11
:linenos:

# See docs at: https://mystmd.org/guide/frontmatter
version: 1
project:
  id: df8b4a16-be6c-4b92-abcc-a95e23b9684a
  # title:
  # description:
  # keywords: []
  # authors: []
  github: https://github.com/2i2c-org/community-docs-template
  # To autogenerate a Table of Contents, run "jupyter-book init --write-toc"
  binder: https://mybinder.org/
  toc:
    - file: content/index.md
    - file: content/kb/index.md
    - file: content/metrics.md
```


As described above, this will enable the launch-button UI.

[mvp]: https://github.com/2i2c-org/infrastructure/issues/5045
[frontmatter]: https://mystmd.org/guide/frontmatter#available-frontmatter-fields
[namecheap]: https://www.namecheap.com/
[cname]: https://en.wikipedia.org/wiki/CNAME_record
[2i2c-org/community-docs-template]: https://github.com/2i2c-org/community-docs-template
[use-template]: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template
[pages]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow
[repo-domain]: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-a-subdomain
