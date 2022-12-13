# Scaling nodepools

When we provision Kubernetes clusters, we setup two, somtimes three, nodepools:

- `core` that contains 'always-on' services such as the hub itself;
- `notebooks` where users' notebook servers are created;
- and optionally, `dask` where dask pods are created for dask-enabled hubs.

By default, we set the `notebook` and `dask` nodepools to scale to zero in order to maximise the cost-effieciency of the cluster.
The drawback of this is that the first user to trigger a nodepool scale-up event is usually left waiting a long time for their server.
There are specific scenarios where we would like to avoid this, such as a hub we are running for a specific event and we can expect a certain number of users and a certain time.
In these scenarios, we often scale-up the nodepools manually before the event so users are not left waiting long periods for their servers.
These sections document how to manually scale a nodepool for each cloud provider.

```{toctree}
aws.md
azure.md
```

```{warning}
Add documentation for how we do this for:
- GKE
- Azure (the "terraform way")
```
