(grafana-dashboards)=
# Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

This section provides information for both engineers and non-engineers about where to find each of 2i2c Grafana deployments, how to get access and what to expect.

(grafana-dashboards:access-grafana)=
## Logging in

Each cluster's Grafana deployment can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the Grafana for the community hubs running on our GCP project is accessible at `grafana.pilot.2i2c.cloud`. Checkout the list of all 2i2c running clusters and their Grafana [here](https://infrastructure.2i2c.org/en/latest/reference/hubs.html).

To access the Grafana dashboards you have two options:

- Get `Viewer` access into the Grafana.

  This is the recommended way of accessing grafana if modifying/creating dashboards is not needed.
  To get access, ask a 2i2c engineer to enable **GitHub authentication** following [](grafana:enable-github-auth) for that particular Grafana (if it's not already) and allow you access.

- Use a **username** and **password** to get `Admin` access into the Grafana.

  These credentials can be accessed using `sops` (see {ref `tc:secrets:sops` for how to set up `sops` on your machine). See [](setup-grafana:log-in) for how to find the credentials information.

(grafana-dashboards:central)=
## The Central Grafana

The Grafana deployment in the `2i2c` cluster is *"the 2i2c central Grafana"* because it ingests data from all of the 2i2c clusters. This is useful because it can be used to access information about all the clusters that 2i2c manages from one central place.

The central Grafana is running at <https://grafana.pilot.2i2c.cloud> and you can use the two authentication mechanisms listed in the [](grafana:access-grafana) section above to access it.

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

(grafana-dashboards:github-auth)=
## (Optional) Enabling GitHub authentication

To enable logging into Grafana using GitHub, follow these steps:

1. Create a GitHub OAuth application following [Grafana's documentation](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/github/#configure-github-oauth-application).
   - Create [a new app](https://github.com/organizations/2i2c-org/settings/applications/new) inside the `2i2c-org`.
   - When naming the application, please follow the convention `<cluster_name>-grafana` for consistency, e.g. `2i2c-grafana` is the OAuth app for the Grafana running in the 2i2c cluster
   - The Homepage URL should match that in the `grafana.ingress.hosts` field of the appropriate cluster `support.values.yaml` file in the `infrastructure` repo. For example, `ghttps://grafana.pilot.2i2c.cloud`
   - The authorisation callback URL is the homepage url appended with `/login/github`. For example, `https://grafana.pilot.2i2c.cloud/login/github`.
   - Once you have created the OAuth app, create a new client ID, generate a client secret and then hold on to these values for a future step

2. Edit using `sops` the encrypted `enc-support.secret.values.yaml` file in the chosen cluster directory and add the credentials created in step one:

   ```yaml
   grafana:
       grafana.ini:
           auth.github:
               client_id: <client-id>
               client_secret: <client-secret>
   ```

3. Edit the `support.values.yaml` file in your chosen cluster directory and add the Grafana GitHub auth config, allowing the specific GitHub organization you wish to allow login.

  ```yaml
  grafana.ini:
    server:
      root_url: https://<grafana.ingress.hosts[0]>
    auth.github:
      enabled: true
      allow_sign_up: false
      scopes: user:email,read:org
      auth_url: https://github.com/login/oauth/authorize
      token_url: https://github.com/login/oauth/access_token
      api_url: https://api.github.com/user
      allowed_organizations: 2i2c-org
  ```

  ```{note}
  Checkout the [Grafana documentation](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/github) for more info about authorizing users using other types of membership than GitHub organizations.
  ```
