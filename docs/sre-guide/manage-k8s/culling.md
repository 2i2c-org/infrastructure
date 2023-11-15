(configure:culling)=
# Cull resources

To improve resource management, every user server that's not actively being used, it's shut down by the [jupyterhub-idle-culler](https://github.com/jupyterhub/jupyterhub-idle-culler) Hub service. Thus, any user pod, will be taken down by the idle culler when they are in an idle state.

Since the server's kernel activity counts as server activity, the idle-culler also operates at a kernel level. This means that if a user leaves a notebook with a running kernel, the kernel will be shut down, if idle for the specified `timeout` period.

## User server culling configuration

To configure the server's different culling options, these options must be specified on a per-hub basis, under the appropriate configuration file in `config/clusters`.

Example:

```yaml
jupyterhub:
  cull:
    # Cull after 30min of inactivity
    every: 300
    timeout: 1800
    # No pods over 12h long
    maxAge: 43200
```

More culling options and information about them can be found in the [idle-culler documentation](https://github.com/jupyterhub/jupyterhub-idle-culler#readme).

## Kernel culling configuration

The kernel culling options are configured through the `jupyter_server_config.json` file, located at `/usr/local/etc/jupyter/jupyter_server_config.json` in the user pod. This file is injected into the pod’s container on startup, by defining its location and content under [`singleuser.extraFiles`](https://zero-to-jupyterhub.readthedocs.io/en/latest/resources/reference.html#singleuser-extrafiles) dictionary.

You can modify the current culling options values, under `singleuser.extraFiles.data`, in the `helm-charts/basehub/values.yaml` file.

Example:

```yaml
singleuser:
  extraFiles:
    jupyter_server_config.json:
      mountPath: /usr/local/etc/jupyter/jupyter_server_config.json
      data:
        MappingKernelManager:
          # shutdown kernels after no activity
          cull_idle_timeout: 3600
          # check for idle kernels this often
          cull_interval: 300
          # a kernel with open connections but no activity still counts as idle
          cull_connected: true
```

```{note}
If a user leaves a notebook with a running kernel, the idle timeout will typically be the cull idle timeout of the server + the cull idle timeout set for the kernel, as culling the kernel will register activity, resetting the `no_activity` timer for the server as a whole.
```
