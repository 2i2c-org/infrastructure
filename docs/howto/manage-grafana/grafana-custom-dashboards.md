# Manage Grafana Dashboards

This how-to guide covers how to manage Grafana dashboards across 2i2c clusters, including how to add new dashboards and managing deployments via CI/CD.

## Existing dashboards

We currently deploy the following dashboards with CI/CD:

- [JupyterHub Default Dashboards](https://github.com/jupyterhub/grafana-dashboards) for all clusters
- [Cloud Cost Dashboards](https://github.com/2i2c-org/jupyterhub-cost-monitoring/) for all AWS clusters

This is handled by the deployer command [`deployer deploy-dashboards`](https://github.com/2i2c-org/infrastructure/blob/main/src/deployer/commands/deploy_dashboards.py), which clones these GitHub repositories and uses the [`./deploy.py`](https://github.com/jupyterhub/grafana-dashboards/blob/main/deploy.py) script to communicate with the Grafana REST API to deploy the dashboards.

This [workflow file](https://github.com/2i2c-org/infrastructure/blob/main/.github/workflows/deploy-grafana-dashboards.yaml) defines the GitHub Action to run the CI/CD job once per day.

## Adding custom dashboards

### Prerequisites

1. Install `go-jsonnet` (the [Grafonnet library](https://github.com/grafana/grafonnet) is vendored with the `jsonnet-builder`).

### Dashboards as code

You can manually prototype and [create Grafana dashboards](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/create-dashboard/) with the UI.

Once you are happy with the dashboard design, you can [export the dashboard as JSON](https://grafana.com/docs/grafana/latest/visualizations/dashboards/share-dashboards-panels/#export-a-dashboard-as-code).

````{tip} Example: Usage Quotas Dashboard as JSON
:class: dropdown
```{include} ./example-usage-quotas.json
:filename: ./example-usage-quotas.json
:lang: json
```
````

### Grafonnet

We can use the JSON as a template to encapsulate the dashboard as [Grafonnet](https://grafana.github.io/grafonnet/index.html) for reproducibility.

In the top-level `dashboards` folder, you can find

- `common.libsonnet` defines common configuration such as datasources, variables and styling
- `*.jsonnet` defines dashboard specific code.

The [Grafonnet documentation](https://grafana.github.io/grafonnet/index.html) is a good resource for learning how to encapsulate your dashboard design as Grafonnet/Jsonnet code.

You can check your work is valid Jsonnet as you develop by running

```{code} bash
jsonnet dashboards/<dashboard-name>.jsonnet
```

````{tip} Example: Usage Quotas Dashboard as Grafonnet
:class: dropdown
```{include} ./usage-quotas.jsonnet
:filename: ./usage-quotas.jsonnet
:lang: go
```
````

## Manually deploy dashboards

To manually deploy your dashboard to a Grafana instance, run the command

```{code} bash
deployer deploy-dashboards --dashboard-type custom $CLUSTER_NAME
```

```{note}
Custom dashboards stored in the top-level `/dashboards` folder are not managed by the CI/CD system. Custom dashboards may not be applicable to all hubs and are therefore manually deployed on a case-by-case basis for now.
```
