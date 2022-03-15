(grafana-dashboards)=
# Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.
This section describes how to use these dashboards for a cluster.

## Access Hub Grafana Dashboards

The Grafana for each cluster can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the Grafana for community hubs running on our GCP project is accessible at `grafana.pilot.2i2c.cloud`.

To access the Grafana dashboards you'll need a **username** and **password**.
These can be accessed using `sops` (see {ref}`tc:secrets:sops` for how to set up `sops` on your machine).
See [](grafana:log-in) for how to find the credentials information.

(grafana:new-grafana)=
## Set up Grafana Dashboards for a cluster

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
prometheusEngressAuthSecret:
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
### Log in to the Grafana dashboard

Eventually, visiting `GRAFANA_URL` will present you with a login page.
Here are the credentials for logging in:

- **username**: `admin`
- **password**: located in `helm-charts/support/enc-support.secret.values.yaml` (`sops` encrypted).

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

Once you've pushed the encrypted `grafana_token` to the GitHub repository, manually trigger the `deploy-grafana-dashboards` workflow using the "Run workflow" button [from here](https://github.com/2i2c-org/infrastructure/actions/workflows/deploy-grafana-dashboards.yaml) to deploy the dashboards.

```{note}
The workflow only runs when manually triggered.

Any re-triggering of the workflow after the initial deployment will overwrite any dashboard created from the Grafana UI and not stored in the [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) repository.
```
