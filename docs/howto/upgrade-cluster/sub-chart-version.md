(upgrade-sub-charts)=
# Upgrade the versions of sub-charts used in our Helm chart

The [basehub helm chart](hub-helm-charts) that 2i2c deploys on their hubs, depends on several upstream helm charts.
This chart needs to be kept up-to-date with the upstream releases so that the communities we serve benefit from the latest features and bug fixes.

Before rolling out a new version of a sub-chart to all of the hubs, we need to make sure that it works as expected. Although manual testing is important, things might still break in production, under high user activity, exposing edge cases that were not considered during testing.

This is why it's important to be able to roll out new versions of sub-charts gradually, starting with a small number of hubs, and then extend it to others, as we gain confidence that the new version is working as expected.

## Bumping the version of a helm sub-chart for all hubs

To bump the version of a sub-chart, we need to edit the `Chart.yaml` file of the `basehub` chart, located at `charts/basehub/Chart.yaml` and update the version of the sub-chart we want to upgrade.

This will bump the version of the sub-chart for all hubs that use the `basehub` chart.

## Bumping the version of a helm sub-chart for a specific hub

### 1. Create a custom `Chart.yaml` file, e.g. `staging-chart.yaml`
  a. **Override a basehub**
    - copy the contents of the original `charts/basehub/Chart.yaml` file into `staging-chart.yaml`
    - update the version of the sub-chart you want to bump.

  b. **Override a legacy daskhub**
    - copy the contents of the original `charts/basehub/Chart.yaml` file into `staging-chart.yaml`
    - override the description and name fields with:
      ```yaml
      description: Deployment Chart for a dask-enabled JupyterHub
      name: daskhub
      ```
    - update the version of the sub-chart you want to bump.

### 2. Configure the hub to use the custom `Chart.yaml` file

Edit the `cluster.yaml` file of the cluster, located at `config/clusters/<cluster-name>/cluster.yaml` and add the path to a custom `Chart.yaml` file under `chart_override`.

Example:
```yaml
hubs:
- name: staging
  display_name: 2i2c staging
  domain: staging.2i2c.cloud
  helm_chart: basehub
  helm_chart_values_files:
  - basehub-common.values.yaml
  - staging.values.yaml
  - enc-staging.secret.values.yaml
  chart_override: staging-chart.yaml
```

In this example, the `staging` hub will use the `staging-chart.yaml` file in the `config/clusters/<cluster-name>` directory, to override the default `Chart.yaml` file of the `basehub` chart.
