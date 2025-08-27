#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'grafonnet/main.libsonnet';
local dashboard = grafonnet.dashboard;
local bc = grafonnet.panel.barChart;
local bg = grafonnet.panel.barGauge;
local var = grafonnet.dashboard.variable;

local common = import './common.libsonnet';

local Hub =
  common.bcOptions
  + bc.new('Hub')
  + bc.panelOptions.withDescription(
    |||
      Shows daily user costs by hub, with a total across `all` hubs shown by default.

      Try toggling the *hub* variable dropdown above to drill down per user costs by hub.
    |||
  )
  + bc.queryOptions.withTargets([
    common.queryTarget
    {
      url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/costs-per-user?from=${__from:date}&to=${__to:date}&hub=$hub',
    },
  ]);


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
