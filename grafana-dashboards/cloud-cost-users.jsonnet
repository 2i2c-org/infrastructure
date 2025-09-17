#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'grafonnet/main.libsonnet';
local dashboard = grafonnet.dashboard;
local bc = grafonnet.panel.barChart;
local bg = grafonnet.panel.barGauge;
local var = grafonnet.dashboard.variable;

local common = import './common.libsonnet';

local Top5 =
  common.bgOptions
  + bg.new('Top 5 users')
  + bg.panelOptions.withDescription(
    |||
      Shows the top 5 users by cost across all hubs and components over the selected time period.
    |||
  )
  + bg.queryOptions.withTargets([
    common.queryUsersTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/costs-per-user?from=${__from:date}&to=${__to:date}',
    },
  ])
  + bg.options.reduceOptions.withValues(true)
  + bg.options.withValueMode('text')
  + bg.standardOptions.color.withMode('thresholds')
  + bg.standardOptions.thresholds.withMode('percentage')
  + bg.standardOptions.thresholds.withSteps([
    {
      color: 'green',
    },
    {
      color: 'red',
      value: 80,
    },
  ])
  + bg.queryOptions.withTransformations([
    bg.queryOptions.transformation.withId('groupBy')
    + bg.queryOptions.transformation.withOptions({
      fields: {
        Cost: {
          aggregations: [
            'sum',
          ],
          operation: 'aggregate',
        },
        User: {
          aggregations: [],
          operation: 'groupby',
        },
        date: {
          aggregations: [],
        },
        user: {
          aggregations: [],
          operation: 'groupby',
        },
        value: {
          aggregations: [
            'sum',
          ],
          operation: 'aggregate',
        },
      },
    }),
    bg.queryOptions.transformation.withId('sortBy')
    + bg.queryOptions.transformation.withOptions({
      sort: [
        {
          desc: true,
          field: 'Cost (sum)',
        },
      ],
    }),
    bg.queryOptions.transformation.withId('limit')
    + bg.queryOptions.transformation.withOptions({
      limitField: '5',
    }),
  ])
;

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
  + bc.panelOptions.withRepeat('hub')
  + bc.panelOptions.withRepeatDirection('v')
;

local Component =
  common.bcOptions
  + bc.new('Component – $component')
  + bc.panelOptions.withDescription(
    |||
      Shows daily user costs grouped by component.

      `compute` and `home storage` costs are user-dependent, whereas other components, not shown, are user-independent (find out more in the Cloud cost attribution dashboard instead). 
    |||
  )
  + bc.queryOptions.withTargets([
    common.queryUsersTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/costs-per-user?from=${__from:date}&to=${__to:date}&component=$component',
    },
  ])
  + bc.panelOptions.withRepeat('component')
  + bc.panelOptions.withRepeatDirection('h')
;

dashboard.new('Cloud costs per user – Grafonnet')
+ dashboard.withUid('cloud-cost-users')
+ dashboard.withTimezone('utc')
+ dashboard.withEditable(true)
+ dashboard.time.withFrom('now-30d')
+ dashboard.withVariables([
  common.variables.hub,
  common.variables.component,
  common.variables.infinity_datasource,
])
+ dashboard.withPanels(
  grafonnet.util.grid.makeGrid(
    [
      Top5,
      Hub,
      Component,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
