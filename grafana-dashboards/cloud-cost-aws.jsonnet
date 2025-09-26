#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'grafonnet/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local var = grafonnet.dashboard.variable;

local common = import './common.libsonnet';


local dailyCosts =
  common.tsOptions
  + ts.new('Daily costs')
  + ts.panelOptions.withDescription(
    |||
      "Costs account" refers to the associated AWS account's total costs, and
      "Costs attributable" refers to the costs that has successfully been
      attributed to 2i2c managed cloud infrastructure.

      There are some costs associated with 2i2c managed cloud infrastructure
      that can't be attributed to it, but they are expected to be small. As an
      example, this panel is presenting data that incurred a small cost to ask
      for, and that cost is an example of what we fail to attribute and is only
      captured in the AWS account's cost.

      If "Costs account" is significantly larger than "Cost attributable", it
      _should_ be because of activity unrelated to 2i2c managed cloud
      infrastructure.

      ---

      **Note**

      - All costs are [unblended costs](https://aws.amazon.com/blogs/aws-cloud-financial-management/understanding-your-aws-cost-datasets-a-cheat-sheet/)
      - All costs are pure usage costs, and doesn't consider credits etc.
    |||
  )
  + ts.queryOptions.withTargets([
    common.queryDailyTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs?from=${__from:date}&to=${__to:date}',
    },
  ]);


local dailyCostsPerHub =
  common.tsOptions
  + ts.new('Daily costs per hub')
  + ts.panelOptions.withDescription(
    |||
      Costs can sometimes be attributed to a specific hub, and that can then be
      seen here.

      "Cost shared" reflect all 2i2c cloud infrastructure attributable costs
      that isn't attributable to a specific hub.

      For hub specific cost attribution, the underlying cloud infrastructure
      needs to setup to be hub specific. Currently compute, home storage, and
      object storage can be setup for specific hubs, but isn't unless explicitly
      requested.

      ---

      **Note**

      - Hub refers to a deployment of a JupyterHub and related services within a
        Kubernetes namespace.
      - All costs are [unblended costs](https://aws.amazon.com/blogs/aws-cloud-financial-management/understanding-your-aws-cost-datasets-a-cheat-sheet/)
      - All costs are pure usage costs, and doesn't consider credits etc.
    |||
  )
  + ts.queryOptions.withTargets([
    common.queryDailyTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs-per-hub?from=${__from:date}&to=${__to:date}',
    },
  ]);


local dailyCostsPerComponent =
  common.tsOptions
  + ts.new('Total daily costs per component')
  + ts.panelOptions.withDescription(
    |||
      Components are human friendly groupings of AWS services, as [defined
      here](https://github.com/2i2c-org/infrastructure/blob/main/helm-charts/jupyterhub-cost-monitoring/mounted-files/const.py#L11-L20).

      ---

      **Note**

      - All costs are [unblended costs](https://aws.amazon.com/blogs/aws-cloud-financial-management/understanding-your-aws-cost-datasets-a-cheat-sheet/)
      - All costs are pure usage costs, and doesn't consider credits etc.
    |||
  )
  + ts.queryOptions.withTargets([
    common.queryComponentTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}',
    },
  ])
  + ts.queryOptions.withTransformations([
    ts.queryOptions.transformation.withId('groupingToMatrix')
    + ts.queryOptions.transformation.withOptions({
      columnField: 'Component',
      emptyValue: 'zero',
      rowField: 'Date',
      valueField: 'Cost',
    }),
  ])
;


local dailyCostsPerComponentAndHub =
  common.tsOptions
  + ts.new('Daily costs per component, for ${hub}')
  + ts.panelOptions.withDescription(
    |||
      Components are human friendly groupings of AWS services, as [defined
      here](https://github.com/2i2c-org/infrastructure/blob/main/helm-charts/jupyterhub-cost-monitoring/mounted-files/const.py#L11-L20).

      **Note**

      - Hub refers to a deployment of a JupyterHub and related services within a
        specific Kubernetes namespace.
      - All costs are [unblended costs](https://aws.amazon.com/blogs/aws-cloud-financial-management/understanding-your-aws-cost-datasets-a-cheat-sheet/)
      - All costs are pure usage costs, and doesn't consider credits etc.
    |||
  )
  + ts.panelOptions.withRepeat('hub')
  + ts.panelOptions.withMaxPerRow(2)
  + ts.queryOptions.withTargets([
    common.queryComponentTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}&hub=$hub',
    },
  ])
  + ts.queryOptions.withTransformations([
    ts.queryOptions.transformation.withId('groupingToMatrix')
    + ts.queryOptions.transformation.withOptions({
      columnField: 'Component',
      emptyValue: 'zero',
      rowField: 'Date',
      valueField: 'Cost',
    }),
  ])
;


// grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/index.html
//
// A dashboard description can be provided, but isn't used much it seems, due to
// that we aren't providing one atm.
// See https://community.grafana.com/t/dashboard-description-is-it-used-anywhere/53273.
//
dashboard.new('Cloud cost attribution')
+ dashboard.withUid('cloud-cost-aws')
+ dashboard.withTimezone('utc')
+ dashboard.withEditable(true)
+ dashboard.time.withFrom('now-30d')
+ dashboard.withVariables([
  common.variables.hub,
  common.variables.infinity_datasource,
])
+ dashboard.withPanels(
  grafonnet.util.grid.makeGrid(
    [
      dailyCosts,
      dailyCostsPerHub,
      dailyCostsPerComponent,
      dailyCostsPerComponentAndHub,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
