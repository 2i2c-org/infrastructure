# Setting up Grafana Dashboards for a hub

This guide will walk through the steps required to setup a suite of Grafana dashboards for a cluster.

## Before you start

Make sure you are authenticated against the correct cloud platform and have selected the correct project to deploy to.

For example, for Google Cloud:

```bash
gcloud auth application-default login
gcloud config set project PROJECT_ID
```

## Deploy the `support` chart

The `support` chart is a helm chart maintained by the 2i2c Engineers that consists of common tools used to support JupyterHub deployments in the cloud.
These tools are [`cert-manager`](https://cert-manager.io/docs/), for automatically provisioning TLS certificates from [Let's Encrypt](https://letsencrypt.org/); [Prometheus](https://prometheus.io/), for scraping and storing metrics from the cluster and hub; and [Grafana](https://grafana.com/), for visualising the metrics retreived by Prometheus.

### Edit your `.cluster.yaml` file


