local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local prometheus = grafonnet.query.prometheus;
local var = grafonnet.dashboard.variable;
local link = grafonnet.dashboard.link;

local common = import './common.libsonnet';

local windowVar =
  var.query.new('window')
  + var.query.queryTypes.withLabelValues('window', 'jupyterhub_memory_usage_byte_hours_total')
  + var.query.withDatasourceFromVariable(common.variables.prometheus)
;

local computeUsage =
  common.tsOptions
  + ts.new('Cumulative compute usage over the last $window days')
  + ts.panelOptions.withDescription(
    |||
      Time series of the cumulative compute usage over the last $window days.
    |||
  )
  + ts.panelOptions.withGridPos(h=13, w=24, x=0, y=0)
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        max(jupyterhub_memory_usage_byte_hours_total{namespace=~"$hub", policy_group!="", username=~"$user"}) by (namespace, username, policy_group, window) / 2^30
      |||
    )
    + prometheus.withLegendFormat(
      |||
        user={{ username }}, policy group={{ policy_group }} ({{ namespace }})
      |||
    ),
  ])
  + ts.options.legend.withCalcs(value=['last'])
  + ts.options.legend.withDisplayMode('table')
  + ts.options.legend.withPlacement('bottom')
  + ts.options.legend.withShowLegend()
  + ts.options.legend.withSortBy('Last')
  + ts.options.legend.withSortDesc()
  + ts.options.tooltip.withMode('single')
  + ts.standardOptions.withUnit('GiB-hr')
;

local failOpens =
  common.tsOptions
  + ts.new('Monitoring - Fail opens')
  + ts.panelOptions.withDescription(
    |||
      This happens when a user server is allowed to launch when the usage quota system is unavailable.
    |||
  )
  + ts.panelOptions.withGridPos(h=8, w=12, x=0, y=13)
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum by (namespace) (changes(jupyterhub_usage_quotas_fail_open_total[30m]))
      |||
    ),
  ])
  + ts.options.legend.withShowLegend(false)
;

local deniedServer =
  common.tsOptions
  + ts.new('Monitoring - Denied server launch')
  + ts.panelOptions.withDescription(
    |||
      Server launch denied due to user exceeding compute quota limit.
    |||
  )
  + ts.panelOptions.withGridPos(h=8, w=12, x=12, y=13)
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        changes((max by (namespace) (jupyterhub_request_duration_seconds_count{code="422",handler="jupyterhub.handlers.pages.SpawnPendingHandler"} or 0 * jupyterhub_request_duration_seconds_count))[30m:1m])
      |||
    )
    + prometheus.withLegendFormat('__auto'),
  ])
;

dashboard.new('Usage Quotas')
+ dashboard.withUid('compute-usage-quotas')
+ dashboard.withTimezone('utc')
+ dashboard.withEditable(true)
+ dashboard.time.withFrom('now-7d')
+ dashboard.withVariables([
  common.variables.prometheus,
  common.variables.hub,
  common.variables.user,
  windowVar,
])
+ dashboard.withLinks([
  link.link.new('Community Hub Guide', 'https://docs.2i2c.org/admin/user-management/compute-quotas/'),
])
+ dashboard.withPanels(
  [
    computeUsage,
    failOpens,
    deniedServer,
  ],
)
