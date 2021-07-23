# Setting up Grafana Dashboards for a cluster

This guide will walk through the steps required to setup a suite of Grafana dashboards for a cluster.

## Deploy the `support` chart

The `support` chart is a helm chart maintained by the 2i2c Engineers that consists of common tools used to support JupyterHub deployments in the cloud.
These tools are [`ingress-nginx`](https://kubernetes.github.io/ingress-nginx/), for controlling ingresses and load balancing; [`cert-manager`](https://cert-manager.io/docs/), for automatically provisioning TLS certificates from [Let's Encrypt](https://letsencrypt.org/); [Prometheus](https://prometheus.io/), for scraping and storing metrics from the cluster and hub; and [Grafana](https://grafana.com/), for visualising the metrics retreived by Prometheus.

### Edit your `*.cluster.yaml` file

Add the following config as a top-level key to your `*.cluster.yaml` file under `/config/hubs` in `pilot-hubs`.
`GRAFANA_URL` should follow the pattern `grafana.<cluster_name>.2i2c.cloud`.

```yaml
support:
  config:
    grafana:
      ingress:
        hosts:
          - GRAFANA_URL
        tls:
          - secretName: grafana-tls
            hosts:
              - GRAFANA_URL
```

### Deploy the `support` chart via the `deployer`

Use the `deployer` tool to deploy the support chart to the cluster.
See {ref}`/howto/operate/manual-deploy` for details on how to setup the tool locally.

```bash
python3 deployer deploy-support CLUSTER_NAME
```

### Setting the DNS A record

Once the `support` chart has been successfully deployed, retrieve the external IP address for the `ingress-nginx` load balancer.

```bash
kubectl --namespace support get svc support-ingress-nginx-controller
```

Add this external IP address to an A record in NameCheap that matches `GRAFANA_URL` that was set in the `*cluster.yaml` file.

**Wait a while for the DNS to propagate!**

Eventually, visiting `GRAFANA_URL` will present you with a login page.
the username is `admin` and the password is located in `support/secrets.yaml` (`sops` encrypted).

## Setting up Grafana Dashboards

Once you have logged into grafana as the admin user, create a new API key.
You can do this by selecting the gear icon from the left-hand menu, and then selecting API keys.
The key you create needs admin permissions.

**Keep this key safe as you won't be able to retrieve it!**

Some default grafana dashboards for JupyterHub can then be deployed using [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).

1. Create a local clone of the repository
2. Install the [`jsonnet` binary](https://github.com/google/jsonnet#packages).
   Homebrew is the best option if you're on MacOS.
   The Python package will not suffice here as we directly call the `jsonnet` library.
3. Follow the instructions in the [Deployment](https://github.com/jupyterhub/grafana-dashboards/blob/main/README.md#deployment) section of the README to create the grafana dashboards
