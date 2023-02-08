(deploy-support-chart)=
# Configure and deploy the `support` chart

The `support` chart is a helm chart maintained by the 2i2c Engineers that consists of common tools used to support JupyterHub deployments in the cloud.
These tools are [`ingress-nginx`](https://kubernetes.github.io/ingress-nginx/), for controlling ingresses and load balancing; [`cert-manager`](https://cert-manager.io/docs/), for automatically provisioning TLS certificates from [Let's Encrypt](https://letsencrypt.org/); [Prometheus](https://prometheus.io/), for scraping and storing metrics from the cluster and hub; and [Grafana](https://grafana.com/), for visualising the metrics retreived by Prometheus.

This section will walk you through how to deploy the support chart on a cluster.

## Create a `support.values.yaml` file in your chosen cluster folder

In the `infrastructure` repo, the full filepath should be: `config/clusters/<cluster_name>/support.values.yaml`.

Add the following helm chart values to your `support.values.yaml` file.
`<grafana-domain>` should follow the pattern `grafana.<cluster_name>.2i2c.cloud`,
and `<prometheus-domain>` should follow the pattern `prometheus.<cluster_name>.2i2c.cloud`.

```yaml
prometheusIngressAuthSecret:
  enabled: true

grafana:
  grafana.ini:
    server:
      root_url: https://<grafana-domain>/
    auth.github:
      enabled: true
      allowed_organizations: 2i2c-org
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

````{warning}
If you are deploying the support chart on an AWS cluster, you **must** enable the `cluster-autoscaler` sub-chart, otherwise the node groups will not automatically scale.
Include the following in your `support.values.yaml` file:

```
cluster-autoscaler:
  enabled: true
  autoDiscovery:
    clusterName: <cluster-name>
  awsRegion: <aws-region>
```
````

## Edit your `cluster.yaml` file

Add the following config as a top-level key to your `cluster.yaml` file.
Note this filepath is _relative_ to the location of your `cluster.yaml` file.

```yaml
support:
  helm_chart_values_files:
    - support.values.yaml
```

## Deploy the `support` chart via the `deployer`

Use the `deployer` tool to deploy the support chart to the cluster.
See [](hubs:manual-deploy) for details on how to setup the tool locally.

```bash
deployer deploy-support CLUSTER_NAME
```

(deploy-support-chart:dns-records)=
## Setting DNS records

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
