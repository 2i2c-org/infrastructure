(grafana-dashboards)=
# Grafana dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

This section provides information for 2i2c staff about where to find each of 2i2c Grafana deployments, how to get access, and what to expect.

```{note}
For granting access to persons external to 2i2c, e.g. community representatives,
see [](grafana-access:invite-link)
```

(grafana-dashboards:access-grafana)=
## Logging into _any_ 2i2c-managed Grafana instance

Each cluster's Grafana deployment can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the Grafana for the community hubs running on our GCP project is accessible at `grafana.pilot.2i2c.cloud`.
Checkout the list of all 2i2c running clusters and their Grafana [here](https://infrastructure.2i2c.org/en/latest/reference/hubs.html).

To access the Grafana dashboards you have two options, detailed in the next sections.

### Get `Viewer` access by authenticating with GitHub

Authenticate with GitHub to get `Viewer` access into the Grafana, _if enabled_.
If enabled, this is the recommended way of accessing Grafana if modifying/creating dashboards is not needed.
To get access, ask a 2i2c engineer to enable **GitHub authentication** following [](grafana-dashboards:github-auth) for that particular Grafana (if it's not already) and allow you access.

### Get `Admin` access using the `admin` username and password

Use the **`admin` username and password** to get `Admin` access into the Grafana.
These credentials can be accessed using `sops` (see  [the team compass documentation](https://compass.2i2c.org/engineering/secrets/#sops-overview) for how to set up `sops` on your machine).
See [](setup-grafana:log-in) for how to find the credentials information.
Alternatively, the password is also stored in the [shared BitWarden account](https://vault.bitwarden.com/#/vault?organizationId=11313781-4b83-41a3-9d35-afe200c8e9f1).
`Admin` access grants you permissions to create and edit dashboards.

(grafana-dashboards:central)=
## The 2i2c Central Grafana

The Grafana deployment in the `2i2c` cluster is *"the 2i2c central Grafana"* because it ingests data from all of the 2i2c clusters. This is useful because it can be used to access information about all the clusters that 2i2c manages from one central place.

The central Grafana is running at <https://grafana.pilot.2i2c.cloud> and you can use the two authentication mechanisms listed in the [](grafana-dashboards:access-grafana) section above to access it.

The dashboards available at <https://grafana.pilot.2i2c.cloud/dashboards> are the default Grafana dashboards from JupyterHub. The following list provides some information about the structure of the dashboards folder in Grafana, but this info is subject to change based on how upstream repository changes. So more information about the metrics and graphs available can be found at [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).

### The `JupyterHub Default Dashboards` Grafana folder structure

Navigating at <https://grafana.pilot.2i2c.cloud/dashboards>, shows a `JupyterHub Default Dashboards` where all the dashboards are available, each of the Grafana panels, being grouped in sub-folders (dashboards) based on the component they are monitoring:

1. **Cluster Information**

  Contains panels with different cluster usage statistics about things like:
    - nodes
    - memory
    - cpu
    - running users per hub in cluster

2. **Global Usage Dashboard**

  This dashboard contains information about the weekly active users we get on each of the clusters we manage.

3. **JupyterHub Dashboard**

  This is the place to find information about the hub usage stats and hub diagnostics, like
  - number of active users
  - user CPU usage distribution
  - user memory usage distribution
  - server start times
  - hub respone latency

  There is also a Panel section about `Anomalous user pods` where pods with high CPU usage or high memory usage are tracked.

4. **NFS and Support Information**

  This provides info about the NFS usage and monitors things like CPU, memory, disk and network usage of the Prometheus instance.

5. **Usage Dashboard**

  This has information about the number of users using the cluster over various periods of time.

6. **Usage Report**

  This provides a report about the memory requests, grouped by username, for notebook nodes and dask-gateway nodes. It also provides a graph that monitors GPU requests per user pod.
