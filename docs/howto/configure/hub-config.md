# Configure each JupyterHub

Each JupyterHub can use its own configuration via the `hubs.yaml` file. This configuration exists under `config.jupyterhub`.
This should be a valid [Zero to JupyterHub](https://z2jh.jupyter.org) configuration. For example, to set a custom memory limit for a hub, you would use:

```yaml
config:
   jupyterhub:
    singleuser:
       memory:
          limit: 1G
```

Here are a few reference pages for JupyterHub Kubernetes configuration:

- {ref}`z2jh:user-environment`
- {ref}`z2jh:user-resources`