local cluster_name = std.extVar('VARS_2I2C_CLUSTER_NAME');
local provider_name = std.extVar('VARS_2I2C_PROVIDER');
local account_id = std.extVar('VARS_2I2C_ACCOUNT_ID');

local makePVCApproachingFullAlert = function(
  summary,
  persistentvolumeclaim,
  threshold,
  severity,
  forInterval='5m',
  labels={},
                                    ) {
  // Structure is documented in https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
  alert: persistentvolumeclaim + ' has ' + threshold + '% of space left',
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
    floor((
      min(kubelet_volume_stats_available_bytes{persistentvolumeclaim='%s'}) by (namespace)
      /
      min(kubelet_volume_stats_capacity_bytes{persistentvolumeclaim='%s'}) by (namespace)
    ) * 100) <= %d
  ||| % [persistentvolumeclaim, persistentvolumeclaim, threshold],
  'for': forInterval,
  labels: {
    cluster: cluster_name,
    severity: severity,
  } + labels,
  annotations: {
    summary: summary,
  },
};

local makeTwoServersStartupFailureAlert = function(
  summary,
  severity,
                                          ) {
  alert: 'At least two servers failed to start in the last 30m',
  expr: |||
    changes(
      (
        max by (namespace) (
          jupyterhub_server_spawn_duration_seconds_count{status="failure"}
        )
      )[30m:1m]
    ) >= 2
  |||,
  'for': '0m',
  labels: {
    provider: 'provider=%s' % [provider_name],
    cluster: 'cluster=%s' % [cluster_name],
    namespace: 'hub={{ $labels.namespace }}',
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local diskIOApproachingSaturation = function(
  name,
  severity,
                                    ) {
  alert: name,
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
};

local makePodRestartAlert = function(
  pod_name,
  summary,
  pod_name_regex,
  severity,
  labels={}
                            ) {
  alert: pod_name + ' pod has restarted',
  expr: |||
    # Count total container restarts with pod name containing 'pod_name_substring'.
    # We sum by pod name (which resets after restart) and namespace, so we don't get all
    # the other labels of the metric in our alert.
      (
            sum by (pod, namespace) (kube_pod_container_status_restarts_total{pod=~"%s"})
          -
            sum by (pod, namespace) (kube_pod_container_status_restarts_total{pod=~"%s"} offset 10m)
      ) >= 1
  ||| % [pod_name_regex, pod_name_regex],
  'for': '5m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  } + labels,
  annotations: {
    summary: summary,
  },
};

local makePodStuckInPendingForTooLongAlert = function(
  summary,
  severity,
                                             ) {
  alert: 'Pod stuck in Pending for at least 30m',
  // Ignore continuous image pre-pullers, as on large images it can take more than 30min to pull
  expr: |||
    max by (namespace, pod) (kube_pod_status_phase{phase="Pending", pod!~"^continuous-image-puller-.*"}) > 0
  |||,
  'for': '30m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local makePodStuckInTerminatingForTooLongAlert = function(
  summary,
  severity,
                                                 ) {
  alert: 'Pod stuck in Terminating for at least 10m',
  expr: |||
    count(kube_pod_deletion_timestamp) by (namespace, pod) * count(kube_pod_status_reason{reason="NodeLost"} == 0) by (namespace, pod)
  |||,
  'for': '10m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local makeUsageQuotasFailOpenAlert = function(
  summary,
  severity,
                                     ) {
  alert: 'Compute usage quotas - At least one fail open detected in the last 30 mins',
  expr: |||
    sum(
      changes(jupyterhub_usage_quotas_fail_open_total[30m])
    ) by (namespace) >= 1
  |||,
  'for': '0m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local makeUsageQuotasPrometheusErrorAlert = function(
  summary,
  severity,
                                            ) {
  alert: 'Compute usage quotas - At least one Prometheus error detected  in the last 30m',
  expr: |||
    sum(
      changes(jupyterhub_usage_quotas_prometheus_error_total[30m])
    ) >= 3
  |||,
  'for': '0m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local makeUsageQuotasServerDeniedAlert = function(
  summary,
  severity,
                                         ) {
  alert: 'Compute usage quotas - At least one server launch denied due to exhausted quota in cluster ' + cluster_name + ' in the last 30 mins',
  expr: |||
    changes(
      (
        max by (namespace) (
          jupyterhub_request_duration_seconds_count{handler="jupyterhub.handlers.pages.SpawnPendingHandler", code="422"}
            or 0*jupyterhub_request_duration_seconds_count # 0 values and absent values are distinct, so we need to 'fill-in' absent values across the time series so that the changes operator acts consistently
          )
        )[30m:1m]
    ) >= 1
  |||,
  'for': '0m',
  labels: {
    cluster: cluster_name,
    severity: severity,
  },
  annotations: {
    summary: summary,
  },
};

local configCostMonitoring = {
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
      'eks.amazonaws.com/role-arn': 'arn:aws:iam::%s:role/jupyterhub_cost_monitoring_iam_role' % account_id,
    },
  },
};

local configFluentBit = {
  serviceAccount: {
    annotations: if provider_name == 'aws' then {
      // See terraform/aws/k8s-event-exporter.tf
      'eks.amazonaws.com/role-arn': 'arn:aws:iam::%s:role/k8s_event_exporter_cloudwatch' % account_id,
    } else {},
  },
};

{
  grafana: {
    serviceAccount: {
      annotations: if provider_name == 'aws' then {
        'eks.amazonaws.com/role-arn': 'arn:aws:iam::%s:role/jupyterhub_grafana_cloudwatch' % account_id,
      } else if provider_name == 'gcp' then {
        'iam.gke.io/gcp-service-account': 'grafana-2i2c-sa@%s.iam.gserviceaccount.com' % account_id,
      } else {},
    },
  },
  prometheus: {
    alertmanager: {
      enabled: true,
      config: {
        route: {
          group_wait: '10s',
          group_interval: '5m',
          receiver: 'pagerduty-pager',
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
              receiver: 'cloudbank-pager',
              matchers: [
                'cluster =~ .*cloudbank.*',
                'alertname =~ .*',
              ],
              // if this one matches, don't check sub-sequent routes
              continue: false,
            },
            {
              receiver: 'known-storage-outage-pager',
              matchers: [
                'cluster =~ .*',
                'alertname =~ ".*has 0% of space left.*"',
              ],
              // if this one matches, don't check sub-sequent routes
              continue: false,
            },
            {
              receiver: 'persistent-storage-pager',
              matchers: [
                'cluster =~ .*',
                'alertname =~ ".*space left.*"',
              ],
            },
            {
              receiver: 'pod-restarts-pager',
              matchers: [
                'cluster =~ .*',
                'alertname =~ ".*pod has restarted"',
              ],
            },
            {
              receiver: 'server-startup-pager',
              matchers: [
                'cluster =~ .*',
                'alertname =~ ".*failed to start.*"',
              ],
            },
            {
              receiver: 'pod-stuck-in-state-pager',
              matchers: [
                'cluster =~ .*',
                'alertname =~ ".*stuck in state.*"',
              ],
            },
            {
              receiver: 'jupyterhub-usage-quotas',
              matchers: [
                'cluster =~ .*',
                'alertname =~ "Compute usage quotas.*"',
              ],
            },
          ],
        },
      },
    },
    serverFiles: {
      'alerting_rules.yml': {
        groups: [
          {
            name: 'PVC available capacity',
            rules: [
              makePVCApproachingFullAlert(
                'Home Directory Disk very close to full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
                'home-nfs',
                10,
                'same day action needed',
              ),
              makePVCApproachingFullAlert(
                'Home Directory Disk is full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
                'home-nfs',
                0,
                'take immediate action',
                '1m',
              ),
              makePVCApproachingFullAlert(
                'Hub Database Disk about to be full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
                'hub-db-dir',
                10,
                'same day action needed'
              ),
              makePVCApproachingFullAlert(
                'Hub Database Disk is full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
                'hub-db-dir',
                0,
                'take immediate action'
              ),
              makePVCApproachingFullAlert(
                'Prometheus Disk about to be full: cluster:%s' % [cluster_name],
                'support-prometheus-server',
                10,
                'same day action needed'
              ),
              makePVCApproachingFullAlert(
                'Prometheus Disk is full: cluster:%s' % [cluster_name],
                'support-prometheus-server',
                0,
                'take immediate action'
              ),
            ],
          },
          {
            name: 'Server Startup Failure',
            rules: [
              makeTwoServersStartupFailureAlert(
                'At least two servers have failed to start in the last 30m: cluster %s hub:{{ $labels.namespace }}' % [cluster_name],
                'immediate action needed',
              ),
            ],
          },
          {
            name: 'Important Pod Restart',
            rules: [
              makePodRestartAlert(
                'jupyterhub-cost-monitoring',
                'jupyterhub-cost-monitoring pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '.*cost-monitoring.*',
                'action needed this week'
              ),
              makePodRestartAlert(
                'jupyterhub-groups-exporter',
                'jupyterhub-groups-exporter pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '.*groups-exporter.*',
                'action needed this week'
              ),
              makePodRestartAlert(
                'jupyterhub-home-nfs',
                'jupyterhub-home-nfs pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '^storage-quota-home-nfs.*',
                'same day action needed'
              ),
              makePodRestartAlert(
                'support-grafana',
                'support-grafana pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '^support-grafana.*',
                'action needed this week'
              ),
              makePodRestartAlert(
                'proxy',
                'proxy pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '^proxy.*',
                'immediate action needed'
              ),
              makePodRestartAlert(
                'support-prometheus-server',
                'support-prometheus-server pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
                '^proxy.*',
                'same day action needed'
              ),
            ],
          },
          {
            name: 'Pod stuck in state for too long',
            rules: [
              makePodStuckInPendingForTooLongAlert(
                'Pod is stuck in Pending state for a suspicious long time',
                'action needed this week'
              ),
              makePodStuckInTerminatingForTooLongAlert(
                'Pod is stuck in Terminating state for a suspicious long time',
                'action needed this week'
              ),
            ],
          },
          {
            name: 'DiskIO saturation',
            rules: [
              diskIOApproachingSaturation(
                'Disk IO approaching saturation',
                'action needed this week'
              ),
            ],
          },
          {
            name: 'Possible application outage',
            rules: [
              makeUsageQuotasFailOpenAlert(
                'Compute usage quotas - Fail open detected on %s:{{ $labels.namespace }} in the last 30 mins' % [cluster_name],
                'same day action needed'
              ),
              makeUsageQuotasPrometheusErrorAlert(
                'Compute usage quotas - At least one Prometheus error detected in %s in the last 30 mins' % [cluster_name],
                'same day action needed'
              ),
              // Temporary alert during initial rollout period
              makeUsageQuotasServerDeniedAlert(
                'Compute usage quotas - Server launch denied on %s:{{ $labels.namespace }} due to exhausted quota in the last 30 mins' % [cluster_name],
                'action needed this week'
              ),
            ],
          },
        ],
      },
    },
  },
  'jupyterhub-cost-monitoring': if provider_name == 'aws' then configCostMonitoring else { enabled: false },
  'fluent-bit': configFluentBit,
}
