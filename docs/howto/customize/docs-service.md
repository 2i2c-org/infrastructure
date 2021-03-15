# Connect static web content with the hub

The 2i2c hubs can be configured to provide static web content as a [JupyterHub service](https://jupyterhub.readthedocs.io/en/stable/reference/services.html), available
at `https://<hub-address>/services/docs`. This can be a great tool to provide hub-specific documentation right from inside the hub.

```{figure} ../../images/docs-service.png
```

To enable the docs service service for a hub:

1. Mark it as *enabled* in `hubs.yaml`, by setting `hubs.<hub>.config.docs_service.enabled` to *True*.
2. Specify the GitHub repository where the static HTML files are hosted, by setting `hubs.<hub>.config.docs_service.repo`.
3. Specify the GitHub branch of the respository where the static HTML files are hosted, by setting `hubs.<hub>.config.docs_service.branch`.

Example config:

```yaml
  config:
    docs_service:
      enabled: true
      repo: https://github.com/<static-web-files-repo-name>
      branch: <branch>
```

```{note}

Depending on what Static Site Generator has been used to generate the website's static content, it **may** or **may not** use relative paths routing by default.
For example, [Sphinx](https://www.sphinx-doc.org/en/master/) handles relative paths by default, whereas, [Hugo](https://gohugo.io/) leaves all [relative URLs unchanged](https://gohugo.io/content-management/urls/#relative-urls).

However, having relative URLS is a **must** in order for the hub docs service to work. Please check with the docs of your SSG of choice and enable relative URLs if they
aren't enabled already.
```
