#!/usr/bin/env -S jsonnet -J ../../vendor
local grafonnet = import '../../vendor/gen/grafonnet-v11.4.0/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local var = grafonnet.dashboard.variable;
local link = grafonnet.dashboard.link;

local common = import './common.libsonnet';

local windowVar =
  var.query.new('queryOptions')
  + var.query.queryTypes.withLabelValues('window', 'jupyterhub_memory_usage_byte_hours_total')
  + var.query.generalOptions.showOnDashboard.withNothing();

local computeUsage =
  ts.new('Cumulative compute usage over the last $windowVar days')
  + ts.panelOptions.withDescription(
    |||
      Time series of the cumulative compute usage over the last $windowVar days.
    |||
  );

dashboard.new('Usage Quotas')
+ dashboard.withUid('compute-usage-quotas')
+ dashboard.withTimezone('utc')
+ dashboard.withEditable(true)
+ dashboard.time.withFrom('now-7d')
+ dashboard.withVariables([
  common.variables.prometheus,
  common.variables.hub,
  windowVar,
])
+ dashboard.withLinks([
  link.link.new('Community Hub Guide', 'https://docs.2i2c.org/admin/user-management/compute-quotas/'),
])
+ dashboard.withPanels(
  grafonnet.util.grid.makeGrid(
    [
      computeUsage,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
