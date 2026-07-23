(deploy-support-chart)=
# Configure and deploy the `support` chart

The `support` chart is a helm chart maintained by the 2i2c Engineers that consists of common tools used to support JupyterHub deployments in the cloud.
These tools are [official NGINX Ingress Controller](https://docs.nginx.com/nginx-ingress-controller/install/helm/open-source/) for controlling ingresses and load balancing; [`cert-manager`](https://cert-manager.io/docs/), for automatically provisioning TLS certificates from [Let's Encrypt](https://letsencrypt.org/); [Prometheus](https://prometheus.io/), for scraping and storing metrics from the cluster and hub; and [Grafana](https://grafana.com/), for visualising the metrics retrieved by Prometheus.

This section will walk you through how to deploy the support chart on a cluster.

```{attention}
If you ran `deployer generate dedicated-cluster ...` during the [new cluster setup](#new-cluster),
then a lot of these files will have already been created for you and you do not
need to recreate them, only update them if required.
```

## Make sure `support.values.yaml` is correctly configured

In the `infrastructure` repo, the full filepath should be: `config/clusters/<cluster_name>/support.values.yaml`.

1. If the cluster is running on GCP or AWS, the deployer should have been generated this file already.

2. If you are deploying the support chart on an Azure cluster, you **must** manually create such a file using the template at `config/clusters/templates/common/support.values.yaml`. Also, you must set an annotation for `nginx-ingress`'s k8s Service resource by including the following in your `support.values.yaml` file:

  ```yaml
  nginx-ingress:
    service:
      annotations:
          # This annotation is a requirement for use in Azure provided
          # LoadBalancer - see https://learn.microsoft.com/en-us/azure/ask/ingress-basic?tabs=azure-cli#basic-configuration
        service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path: /healthz
  ```

## Edit your `cluster.yaml` file

Add the following config as a top-level key to your `cluster.yaml` file.
Note this filepath is _relative_ to the location of your `cluster.yaml` file.

```yaml
support:
  helm_chart_values_files:
    - support.values.yaml
```

(deploy-support-chart:manual)=
## Deploy the `support` chart via the `deployer`

Use the `deployer` tool to deploy the support chart to the cluster.
See [](#hubs:manual-deploy) for details on how to setup the tool locally.

```bash
deployer deploy-support $CLUSTER_NAME
```

(deploy-support-chart:dns-records)=
## Setting DNS records

Once the `support` chart has been successfully deployed, retrieve the external IP address for the `cluster-entrypoint` load balancer.

```bash
deployer use-cluster-credentials $CLUSTER_NAME
```

```bash
kubectl --namespace=support get service/cluster-entrypoint --template='{{$ingress := (index .status.loadBalancer.ingress 0)}}{{or $ingress.hostname $ingress.ip}}'
```

Add DNS records for the `2i2c.cloud` domain [under "Advanced DNS" in
Namecheap.com](https://ap.www.namecheap.com/Domains/DomainControlPanel/2i2c.cloud/advancedns):

```{important}
TTL for DNS entries should be set to 5m (300s) rather than the default 30m on Namecheap.
```

1. `<cluster-name>`, used for the primary hub (if it exists).
2. `*.<cluster-name>`, for all other hubs, grafana and prometheus
   instances.

Use an `A` record when we point to an external IP address (GCP, Azure), and a
`CNAME` record when we point to another domain (AWS).

```{note}
It may take a while for this configuration to propagate to all devices making
DNS lookups. After that, cert-manager needs to do its job to acquire HTTPS
certificates. And finally, the nginx-ingress server that makes use of the HTTPS
certificates needs to reload to use the acquired certificates.
```
