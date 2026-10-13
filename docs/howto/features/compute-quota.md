(howto:configure-compute-quota)=

# Configure compute quotas

This guide explains how to enable and configure compute quotas using the [`jupyterhub-usage-quotas`](https://github.com/2i2c-org/jupyterhub-usage-quotas) system.

```{tip}
For details on general configuration, see [JupyterHub Usage Quotas -- Multi-cluster setups](https://jupyterhub-usage-quotas.readthedocs.io/en/latest/howto/deploy/#multi-cluster-setups).
```

## How to enable

The entry `12-conditional-usage-quotas` under the `jupyterhub.hub.extraConfig` key in the `basehub/values.yaml` file conditionally enables the JupyterHub service running the usage dashboard. This service is opt-in by adding

```yaml
basehub:
  jupyterhub:
    custom:
      usageQuotas:
        enabled: true
```

to a hub's `values.yaml` file. The service is currently opt out for all Cloudbank hub's due to issues with CI/CD deployment for this cluster, however this deployment strategy will be updated when [this issue](https://github.com/2i2c-org/jupyterhub-usage-quotas/issues/90) is fixed.

The quota manager itself is a library is unconditionally installed in all hub images through the `helm-charts/images/hub/requirements.txt` file.

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

The general grafonnet code to define the usage quotas Grafana dashboard can be found in `/dashboards/usage-quotas.jsonnet`. See [Manually deploy dashboards](../manage-grafana/grafana-custom-dashboards.md#manually-deploy-dashboards) for how to deploy this to communities with compute usage quotas enabled.
