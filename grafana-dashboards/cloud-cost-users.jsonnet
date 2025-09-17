#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'grafonnet/main.libsonnet';
local dashboard = grafonnet.dashboard;
local bc = grafonnet.panel.barChart;
local bg = grafonnet.panel.barGauge;
local var = grafonnet.dashboard.variable;

local common = import './common.libsonnet';

local Hub =
  common.bcOptions
  + bc.new('Hub – $hub')
  + bc.panelOptions.withDescription(
    |||
      Shows daily user costs by hub, with a total across `all` hubs shown by default.

      Try toggling the *hub* variable dropdown above to drill down per user costs by hub.
    |||
  )
  + bc.queryOptions.withTargets([
    common.queryUsersTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/costs-per-user?from=${__from:date}&to=${__to:date}&hub=$hub',
    },
  ])
  + bc.queryOptions.withTransformations([
    bc.queryOptions.transformation.withId('formatTime')
    + bc.queryOptions.transformation.withOptions({
      outputFormat: 'MMM DD',
      timeField: 'Date',
      useTimezone: true,
    }),
    bc.queryOptions.transformation.withId('groupBy')
    + bc.queryOptions.transformation.withOptions({
      fields: {
        Component: {
          aggregations: [],
        },
        Cost: {
          aggregations: [
            'sum',
          ],
          operation: 'aggregate',
        },
        Date: {
          aggregations: [],
          operation: 'groupby',
        },
        User: {
          aggregations: [],
          operation: 'groupby',
        },
      },
    }),
    bc.queryOptions.transformation.withId('groupingToMatrix')
    + bc.queryOptions.transformation.withOptions({
      columnField: 'User',
      emptyValue: 'zero',
      rowField: 'Date',
      valueField: 'Cost (sum)',
    }),
  ])
;


dashboard.new('Cloud costs per user – Grafonnet')
+ dashboard.withUid('cloud-cost-users')
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
      Hub,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
