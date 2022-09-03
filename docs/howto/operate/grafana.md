(grafana-dashboards)=
# Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

The following sections describe how to access, use and deploy these dashboards for a cluster.

## 1. How to access and use the Grafana Dashboards

This section provides information for both engineers and non-engineers about where to find each of 2i2c Grafana deployments, how to get access and what to expect.

(grafana:access-grafana)=
### Logging in

Each cluster's Grafana deployment can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the Grafana for the community hubs running on our GCP project is accessible at `grafana.pilot.2i2c.cloud`.

To access the Grafana dashboards you have two options:

- Get `Viewer` access into the Grafana.
  This is the recommended way of accessing grafana if modifying/creating dashboards is not needed.
  To get access, ask a 2i2c engineer to enable **GitHub authentication** following [](grafana:enable-github-auth) for that particular Grafana (if it's not already) and allow you access.

- Use a **username** and **password** to get `Admin` access into the Grafana.
  These credentials can be accessed using `sops` (see {ref `tc:secrets:sops` for how to set up `sops` on your machine). See [](grafana:log-in) for how to find the credentials information.

### The Central Grafana

The Grafana deployment in the `2i2c` cluster is *"the 2i2c central Grafana"* because it ingests data from all of the 2i2c clusters. This is useful because it can be used to access information about all the clusters that 2i2c manages from one central place.

The central Grafana is running at https://grafana.pilot.2i2c.cloud and you can use the two authentication mechanisms listed in the [](grafana:access-grafana) section above to access it.

The dashboards available at https://grafana.pilot.2i2c.cloud/dashboards are the default Grafana dashboards from JupyterHub. The following list provides some information about the structure of the dashboards folder in Grafana, but this info is subject to change based on how upstream repository changes. So more information about the metrics and graphs available can be found at [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).

#### The `JupyterHub Default Dashboards` Grafana folder structure

Navigating at https://grafana.pilot.2i2c.cloud/dashboards, shows a `JupyterHub Default Dashboards` where all the dashboards are available, each of the Grafana panels, being grouped in sub-folders (dashboards) based on the component they are monitoring:

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

(grafana:new-grafana)=
## 2. Set up Grafana Dashboards for a cluster

This guide will walk through the steps required to setup a suite of Grafana dashboards for a cluster.

### Deploy the `support` chart

The `support` chart is a helm chart maintained by the 2i2c Engineers that consists of common tools used to support JupyterHub deployments in the cloud.
These tools are [`ingress-nginx`](https://kubernetes.github.io/ingress-nginx/), for controlling ingresses and load balancing; [`cert-manager`](https://cert-manager.io/docs/), for automatically provisioning TLS certificates from [Let's Encrypt](https://letsencrypt.org/); [Prometheus](https://prometheus.io/), for scraping and storing metrics from the cluster and hub; and [Grafana](https://grafana.com/), for visualising the metrics retreived by Prometheus.

#### Create a `support.values.yaml` file in your chosen cluster folder

In the `infrastructure` repo, the full filepath should be: `config/clusters/<cluster_name>/support.values.yaml`.

Add the following helm chart values to your `support.values.yaml` file.
`<grafana-domain>` should follow the pattern `grafana.<cluster_name>.2i2c.cloud`,
and `<prometheus-domain>` should follow the pattern `prometheus.<cluster_name>.2i2c.cloud`.

```yaml
prometheusIngressAuthSecret:
  enabled: true

grafana:
  ingress:
    hosts:
      - <grafana-domain>
    tls:
      - secretName: grafana-tls
        hosts:
          - <grafana-domain>

prometheus:
  server:
    ingress:
      enabled: true
      hosts:
        - <prometheus-domain>
      tls:
        - secretName: prometheus-tls
          hosts:
            - <prometheus-domain>
```

#### Create a `enc-support.secret.values.yaml` file

Only 2i2c staff + our centralized grafana should be able to access the
prometheus data on a cluster from outside the cluster. The [basic auth](https://kubernetes.github.io/ingress-nginx/examples/auth/basic/)
feature of nginx-ingress is used to restrict this. A `enc-support.secret.values.yaml`
file is used to provide these secret credentials.

```yaml
prometheusIngressAuthSecret:
  username: <output of pwgen -s 64 1>
  password: <output of pwgen -s 64 1>
```

```{note}
We use the [pwgen](https://linux.die.net/man/1/pwgen) program, commonly
installed by default in many operating systems, to generate the password.
```

Once you create the file, encrypt it in-place with `sops --in-place --encrypt <file-name>`.


#### Edit your `cluster.yaml` file

Add the following config as a top-level key to your `cluster.yaml` file.
Note this filepath is _relative_ to the location of your `cluster.yaml` file.

```yaml
support:
  helm_chart_values_files:
    - support.values.yaml
    - enc-support.secret.values.yaml
```

#### (Optional) Enable GitHub authentication

You can enable users and/community members to authenticate Grafana, through GitHub by following the next steps:

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

#### Deploy the `support` chart via the `deployer`

Use the `deployer` tool to deploy the support chart to the cluster.
See [](operate:manual-deploy) for details on how to setup the tool locally.

```bash
python3 deployer deploy-support CLUSTER_NAME
```

#### Setting DNS records

Once the `support` chart has been successfully deployed, retrieve the external IP address for the `ingress-nginx` load balancer.

```bash
kubectl --namespace support get svc support-ingress-nginx-controller
```

Add the following DNS records via Namecheap.com:

1. `<cluster-name>.2i2c.cloud`, used for the primary hub (if it exists).
2. `*.<cluster-name>.2i2c.cloud`, for all other hubs, grafana and prometheus
   instances.

The DNS records should be `A` records if using GCP or Azure (where external IP is an
IPv4 address), or `CNAME` records if using AWS (where external IP is a domain name).

**Wait a while for the DNS to propagate!**

(grafana:log-in)=
### Log in to the cluster-specific Grafana dashboard

Eventually, visiting `GRAFANA_URL` will present you with a login page.
Here are the credentials for logging in:

- **username**: `admin`
- **password**: located in `helm-charts/support/enc-support.secret.values.yaml` (`sops` encrypted).

### Register the cluster's Prometheus Server with the central Grafana

Once you have deployed the support chart, you must also register this cluster as a datasource for the central Grafana dashboard. This will allow you to visualize cluster statistics not only from the cluster-specific Grafana deployement but also from the central dashboard, that aggregates data from all the clusters.

Run the `update_central_grafana_datasources.py` script in the deployer to let the central Grafana know about this new prometheus server:

```
$ python3 deployer/update_central_grafana_datasources.py <grafana-cluster-name>
```

Where:
- <grafana-cluster-name> is the name of the cluster where the central Grafana lives. Right now, this defaults to "2i2c".

### Setting up Grafana Dashboards

Once you have logged into grafana as the admin user, create a new API key.
You can do this by selecting the gear icon from the left-hand menu, and then selecting API keys.
The key you create needs admin permissions.

**Keep this key safe as you won't be able to retrieve it!**

Create the file `config/clusters/<cluster>/grafana-token.secret.yaml` with the following content.

```yaml
grafana_token: PASTE_YOUR_API KEY HERE
```

Then encrypt this file using `sops` like so:

```bash
sops --output config/clusters/<cluster>/enc-grafana-token.secret.yaml --encrypt config/clusters/<cluster>/grafana-token.secret.yaml
```

The encrypted file can now be committed to the repository.

This key will be used by the [`deploy-grafana-dashboards` workflow](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-grafana-dashboards.yaml) to deploy some default grafana dashboards for JupyterHub using [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).

### Enable GitHub authentication

You can enable users and/community members to authenticate a Grafana, through GitHub.

### Deploying the Grafana Dashboards from CI/CD

Once you've pushed the encrypted `grafana_token` to the GitHub repository, it will be possible to manually trigger the `deploy-grafana-dashboards` workflow using the "Run workflow" button [from here](https://github.com/2i2c-org/infrastructure/actions/workflows/deploy-grafana-dashboards.yaml) to deploy the dashboards.

You will first need to add the name of the cluster as a matrix entry in the [`deploy-grafana-dashboards.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/008ae2c1deb3f5b97d0c334ed124fa090df1f0c6/.github/workflows/deploy-grafana-dashboards.yaml#L12) and commit the change to the repo.

```{note}
The workflow only runs when manually triggered.

Any re-triggering of the workflow after the initial deployment will overwrite any dashboard created from the Grafana UI and not stored in the [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) repository.
```
