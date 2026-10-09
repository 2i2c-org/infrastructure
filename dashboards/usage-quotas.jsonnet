local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local tb = grafonnet.panel.table;
local prometheus = grafonnet.query.prometheus;
local var = grafonnet.dashboard.variable;
local link = grafonnet.dashboard.link;

local common = import './common.libsonnet';

local windowVar =
  var.query.new('window')
  + var.query.queryTypes.withLabelValues('window', 'jupyterhub_memory_usage_byte_hours_total')
  + var.query.withDatasourceFromVariable(common.variables.prometheus)
  + var.query.generalOptions.withDescription('Rolling window (days) quota policy is applied over.')
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
        max(jupyterhub_memory_usage_byte_hours_total{namespace=~"$hub", policy_group!="", username=~"$user", window=~"$window"}) by (namespace, username, policy_group, window) / 2^30
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

local computeLimits =
  tb.new('Compute usage policies')
  + tb.panelOptions.withDescription(
    |||
      Compute usage quota limits individually applied to policy group members.
    |||
  )
  + tb.panelOptions.withGridPos(h=8, w=10, x=0, y=13)
  + tb.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        avg(jupyterhub_memory_limit_byte_hours_total{namespace=~"$hub", window=~"$window"}) by (namespace, window, policy_group) / 2^30
      |||
    )
    + prometheus.withInstant()
    + prometheus.withLegendFormat('{{policy_group}} ({{namespace}}) – {{window}} day window'),
  ])
  + tb.queryOptions.withTransformations([
    tb.queryOptions.transformation.withId('reduce')
    + tb.queryOptions.transformation.withOptions({
      labelsToFields: false,
      reducers: [
        'lastNotNull',
      ],
    }),
    tb.queryOptions.transformation.withId('organize')
    + tb.queryOptions.transformation.withOptions({
      renameByName: {
        Field: 'policy group',
        'Last *': 'quota limit (GiB-hr)',
      },
    }),
  ])
  + tb.standardOptions.withOverrides(
    [
      {
        matcher: {
          id: 'byName',
          options: 'policy group',
        },
        properties: [
          {
            id: 'custom.width',
            value: 293,
          },
        ],
      },
    ]
  )
;

local deniedServer =
  common.tsOptions
  + ts.new('Monitoring - Denied server launch')
  + ts.panelOptions.withDescription(
    |||
      Server launch denied due to user exceeding compute quota limit.
    |||
  )
  + ts.panelOptions.withGridPos(h=8, w=7, x=10, y=13)
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

local failOpens =
  common.tsOptions
  + ts.new('Monitoring - Fail opens')
  + ts.panelOptions.withDescription(
    |||
      This happens when a user server is allowed to launch when the usage quota system is unavailable.
    |||
  )
  + ts.panelOptions.withGridPos(h=8, w=7, x=17, y=13)
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
    computeLimits,
    deniedServer,
    failOpens,
  ],
)
