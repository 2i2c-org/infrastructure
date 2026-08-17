(howto:configure-compute-quota)=

# Configure compute quotas

This guide explains how to enable and configure compute quotas using the [`jupyterhub-usage-quotas`](https://github.com/2i2c-org/jupyterhub-usage-quotas) system.

```{tip}
For details on general configuration, see [JupyterHub Usage Quotas -- Multi-cluster setups](https://jupyterhub-usage-quotas.readthedocs.io/en/latest/howto/deploy/#multi-cluster-setups).
```

## Conditionally enabled in Jsonnet

The compute quota system is enabled for all hubs except for hubs such as BinderHubs, etc. See the conditional `is_usage_quotas_hub` defined in the Jsonnet [`basehub/values.jsonnet`](https://github.com/2i2c-org/infrastructure/blob/5761a5b7038557dce8f7b6c6574ba0b6c6d8b1bb/helm-charts/basehub/values.jsonnet#L12) for hub name patterns that are excluded from usage quota deployments.

## Add a compute quota policy

See [JupyterHub Usage Quotas -- Policy configuration](https://jupyterhub-usage-quotas.readthedocs.io/en/latest/explanation/technical/#policy-configuration).

## Enable usage quota dashboard components

In the [usage quota dashboard](https://jupyterhub-usage-quotas.readthedocs.io/en/latest/howto/quickstart/#usage-quota-dashboard), the **Compute** component is [disabled by default](https://github.com/2i2c-org/infrastructure/blob/5761a5b7038557dce8f7b6c6574ba0b6c6d8b1bb/helm-charts/basehub/values.yaml#L910) since compute quota policies do not exist by default. You can enable this component for each individual hub with a compute policy applied.

```{code} yaml
:filename: config/clusters/$CLUSTER_NAME/$HUB_NAME.values.yaml
hub:
  config:
    UsageViewer:
      enable_compute: true
```

## Grafana Dashboards

The general grafonnet code to define the usage quotas Grafana dashboard is a work-in-progress, however you can [manually export](https://grafana.com/docs/grafana/latest/visualizations/dashboards/share-dashboards-panels/#export-a-dashboard-as-code) the prototype dashboard definition from the Earthscope Grafana instance and import this into another Grafana instance.
