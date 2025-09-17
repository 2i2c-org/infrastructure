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

local TotalHub =
  common.bgOptions
  + bg.new('Total by Hub')
  + bc.panelOptions.withDescription(
    |||
      Total costs by hub are summed over the time period selected.

      - prod: the main production hub, e.g. <your-community>.2i2c.cloud
      - staging: a hub for testing, e.g. staging.<your-community>.2i2c.cloud
      - workshop: a hub for events such as workshops and tutorials, e.g. workshop.<your-community>.2i2c.cloud
    |||
  )
  + bg.queryOptions.withTargets([
    common.queryHubTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs-per-hub?from=${__from:date}&to=${__to:date}',
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
        Hub: {
          aggregations: [],
          operation: 'groupby',
        },
      },
    }),
    bg.queryOptions.transformation.withId('transpose'),
    bg.queryOptions.transformation.withId('organize')
    + bg.queryOptions.transformation.withOptions({
      excludeByName: {
        shared: true,
        support: true,
      },
      includeByName: {},
      indexByName: {
        Field: 0,
        prod: 1,
        shared: 4,
        staging: 2,
        workshop: 3,
      },
      renameByName: {
        shared: 'support',
      },
    }),
  ])
  + bg.standardOptions.color.withMode('continuous-BlYlRd')
;

local TotalComponent =
  common.bgOptions
  + bg.new('Total by Component')
  + bg.panelOptions.withDescription(
    |||
      Total costs by component are summed over the time period selected.

      - compute: CPU and memory of user nodes
      - home storage: storage disks for user directories
      - networking: load balancing and virtual private cloud
      - object storage: cloud storage, e.g. AWS S3
      - support: compute and storage for support functions
    |||
  )
  + bg.queryOptions.withTargets([
    common.queryComponentTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}',
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
        Component: {
          aggregations: [],
          operation: 'groupby',
        },
      },
    }),
    bg.queryOptions.transformation.withId('transpose'),
    bg.queryOptions.transformation.withId('organize')
    + bg.queryOptions.transformation.withOptions({
      indexByName: {
        Field: 0,
        compute: 1,
        fixed: 5,
        'home storage': 2,
        networking: 4,
        'object storage': 3,
      },
      renameByName: {
        fixed: 'support',
      },
    }),
  ])
  + bg.standardOptions.color.withMode('continuous-BlYlRd')
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
      TotalHub,
      TotalComponent,
      Hub,
      Component,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
