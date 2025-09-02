local cluster_name = std.extVar('VARS_2I2C_CLUSTER_NAME');
local provider_name = std.extVar('VARS_2I2C_PROVIDER');

function(VARS_2I2C_AWS_ACCOUNT_ID=null)
  local makePVCApproachingFullAlert = function(
    summary,
    persistentvolumeclaim,
    threshold,
    severity,
    forInterval='5m',
    labels={},
                                      ) {
    // Structure is documented in https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
    name: persistentvolumeclaim + ' has ' + threshold * 100 + '% of space left',
    rules: [
      {
        alert: persistentvolumeclaim + ' has ' + threshold * 100 + '% of space left',
        expr: |||
          # We use min() here for two reasons:
          # 1. kubelet_volume_stats_* is reported once per each node the PVC is mounted on, which can be
          #    multiple nodes if the PVC is ReadWriteMany (like any NFS mount). We only want alerts once per
          #    PVC, rather than once per node.
          # 2. This metric has a *ton* of labels, that can be cluttering and hard to use on pagerduty. We use
          #    min() to select only the labels we care about, which is the namespace it is on.
          #
          # We could have used any aggregating function, but use min because we expect the numbers on the
          # PVC to be the same on all nodes.
          min(kubelet_volume_stats_available_bytes{persistentvolumeclaim='%s'}) by (namespace)
          /
          min(kubelet_volume_stats_capacity_bytes{persistentvolumeclaim='%s'}) by (namespace)
          <= %.2f
        ||| % [persistentvolumeclaim, persistentvolumeclaim, threshold],
        'for': forInterval,
        labels: {
          cluster: cluster_name,
          severity: severity,
        } + labels,
        annotations: {
          summary: summary,
        },
      },
    ],
  };

  local makeServerStartupFailureAlert = function(
    name,
    summary,
    severity,
    labels={},
                                        ) {
    // Structure is documented in https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
    name: name,
    rules: [
      {
        alert: name,
        expr: |||
          # We trigger any time there is a server startup failure, for any reason.
          # The 'min' is to reduce the labels being passed to only the necessary ones
          min(
            jupyterhub_server_spawn_duration_seconds_count{status="failure"} > 0
          ) by (namespace)
        |||,
        'for': '1m',
        labels: {
          cluster: cluster_name,
          severity: severity,
        } + labels,
        annotations: {
          summary: summary,
        },
      },
    ],
  };

  local diskIOApproachingSaturation = function(
    name,
    severity,
                                      ) {
    name: name,
    rules: [
      {
        alert: 'DiskIOApproachingSaturation',
        expr: |||
          # We calculate the utilization for any given disk on our cluster,
          # and alert if that goes over 80%. This is primarily here to catch
          # overutilization of NFS host disk, which may cause serious outages.
          # https://brian-candler.medium.com/interpreting-prometheus-metrics-for-linux-disk-i-o-utilization-4db53dfedcfc
          # has helpful explanations for this metric, and why this particular query
          # is utilization %.
          sum(
            rate(
              node_disk_io_time_seconds_total[5m]
            )
          ) by (device, node) > 0.8
        |||,
        // Don't fire unless the alert fires for 15min, to reduce possible false alerts
        'for': '15m',
        labels: {
          cluster: cluster_name,
          severity: severity,
        },
        annotations: {
          summary: 'Disk {{ $labels.device }} on node {{ $labels.node }} is approaching saturation on cluster %s' % [cluster_name],
        },
      },
    ],
  };

  local makePodRestartAlert = function(
    name,
    summary,
    pod_name_substring,
    severity,
    labels={}
                              ) {
    name: name,
    rules: [
      {
        alert: name,
        expr: |||
          # Count total container restarts with pod name containing 'pod_name_substring'.
          # We sum by pod name (which resets after restart) and namespace, so we don't get all
          # the other labels of the metric in our alert.
          sum(kube_pod_container_status_restarts_total{pod=~'.*%s.*'}) by (pod, namespace) >= 1
        ||| % [pod_name_substring],
        'for': '5m',
        labels: {
          cluster: cluster_name,
          severity: severity,
        } + labels,
        annotations: {
          summary: summary,
        },
      },
    ],
  };

  local configCostMonitoring = function(VARS_2I2C_AWS_ACCOUNT_ID) {
    enabled: true,
    extraEnv: [
      {
        name: 'CLUSTER_NAME',
        value: cluster_name,
      },
    ],
    serviceAccount: {
      annotations: {
        // See terraform/aws/cost-monitoring.tf
        'eks.amazonaws.com/role-arn': 'arn:aws:iam::%s:role/jupyterhub_cost_monitoring_iam_role' % VARS_2I2C_AWS_ACCOUNT_ID,
      },
    },
  };

  {
    prometheus: {
      alertmanager: {
        enabled: true,
        config: {
          route: {
            group_wait: '10s',
            group_interval: '5m',
            receiver: 'pagerduty',
            group_by: [
              // Deliver alerts individually for each alert as well as each namespace
              // an alert is for. Each alertmanager only handles one cluster so 'cluster'
              // is a bit obsolete here. Still, see if it fixes the grouping issues we have.
              'alertname',
              'cluster',
              'namespace',
            ],
            repeat_interval: '3h',
            routes: [
              {
                receiver: 'pagerduty',
                matchers: [
                  // We want to match all alerts, but not add additional labels as they
                  // clutter the view. So we look for the presence of the 'cluster' label, as that
                  // is present on all alerts we have. This makes the 'cluster' label *required* for
                  // all alerts if they need to come to pagerduty.
                  'cluster =~ .*',
                ],
              },
              {
                receiver: 'persistent-storage',
                matchers: [
                  'cluster =~ .*',
                  'name =~ .*space left',
                ],
              },
            ],
          },
        },
      },
      serverFiles: {
        'alerting_rules.yml': {
          groups: [
            // Persistent storage related alerts
            makePVCApproachingFullAlert(
              'Take action! Home Directory Disk very close to full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
              'home-nfs',
              0.1,
              'same day action needed',
            ),
            makePVCApproachingFullAlert(
              'Take action! Home Directory Disk very close to full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
              'home-nfs',
              0,
              'take immediate action',
              '1m',
            ),
            makePVCApproachingFullAlert(
              'Hub Database Disk about to be full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
              'hub-db-dir',
              0.1,
              'same day action needed'
            ),
            makePVCApproachingFullAlert(
              'Prometheus Disk about to be full: cluster:%s' % [cluster_name],
              'support-prometheus-server',
              0.1,
              'same day action needed'
            ),
            // User server startup related alerts
            makeServerStartupFailureAlert(
              'Server Startup Failed',
              'Outage alert: Server Startup failed: cluster %s hub:{{ $labels.namespace }}' % [cluster_name],
              'same day action needed'
            ),
            // Pod restarts for important pods
            makePodRestartAlert(
              'Groups exporter pod has restarted',
              'jupyterhub-groups-exporter pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
              'groups-exporter',
              'action needed this week'
            ),
            makePodRestartAlert(
              'NFS Server Pod has restarted',
              'jupyterhub-home-nfs pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
              'storage-quota-home-nfs',
              'same day action needed'
            ),
            // General disk IO saturation alert
            diskIOApproachingSaturation(
              'Disk IO approaching saturation',
              'action needed this week'
            ),
          ],
        },
      },
    },
    'jupyterhub-cost-monitoring': if provider_name == 'aws' then configCostMonitoring(VARS_2I2C_AWS_ACCOUNT_ID) else { enabled: false },
  }
