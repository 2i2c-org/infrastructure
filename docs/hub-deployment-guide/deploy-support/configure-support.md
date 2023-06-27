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

```yaml
cluster-autoscaler:
  enabled: true
  autoDiscovery:
    clusterName: <cluster-name>
  awsRegion: <aws-region>
```
````

````{warning}
If you are deploying the support chart on an Azure cluster, you **must** set an annotation for `ingress-nginx`'s k8s Service resource.
Include the following in your `support.values.yaml` file:

```yaml
ingress-nginx:
  controller:
    service:
      annotations:
        # This annotation is a requirement for use in Azure provided
        # LoadBalancer.
        #
        # ref: https://learn.microsoft.com/en-us/azure/aks/ingress-basic?tabs=azure-cli#basic-configuration
        # ref: https://github.com/Azure/AKS/blob/master/CHANGELOG.md#release-2022-09-11
        # ref: https://github.com/Azure/AKS/issues/2907#issuecomment-1109759262
        # ref: https://github.com/kubernetes/ingress-nginx/issues/8501#issuecomment-1108428615
        #
        service.beta.kubernetes.io/azure-load-balancer-health-probe-request-path: /healthz
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
deployer deploy-support $CLUSTER_NAME
```

(deploy-support-chart:dns-records)=
## Setting DNS records

Once the `support` chart has been successfully deployed, retrieve the external IP address for the `ingress-nginx` load balancer.

```bash
kubectl --namespace=support get service support-ingress-nginx-controller
```

Add DNS records for the `2i2c.cloud` domain [under "Advanced DNS" in
Namecheap.com](https://ap.www.namecheap.com/Domains/DomainControlPanel/2i2c.cloud/advancedns):

1. `<cluster-name>.2i2c.cloud.`, used for the primary hub (if it exists).
2. `*.<cluster-name>.2i2c.cloud.`, for all other hubs, grafana and prometheus
   instances.

Use an `A` record when we point to an external IP addresse (GCP, Azure), and a
`CNAME` record when we point to another domain (AWS).

```{note}
It may take a while for this configuration to propagate to all devices making
DNS lookups. After that, cert-manager needs to do its job to acquire HTTPS
certificates. And finally, the ingress-nginx server that makes use of the HTTPS
certificates needs to reload to use the acquired certificates.
```
