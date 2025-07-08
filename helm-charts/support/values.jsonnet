local cluster_name = std.extVar('2I2C_VARS.CLUSTER_NAME');

local makePVCApproachingFullAlert = function(
  name,
  summary,
  persistentvolumeclaim,
  labels={},
                                    ) {
  // Structure is documented in https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
  name: name,
  rules: [
    {
      alert: name,
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
        < 0.1
      ||| % [persistentvolumeclaim, persistentvolumeclaim],
      'for': '5m',
      labels: {
        cluster: cluster_name,
      } + labels,
      annotations: {
        summary: summary,
      },
    },
  ],
};

local diskIOApproachingSaturation = {
  name: 'DiskIOApproachingSaturation',
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
        page: 'yuvipanda',  // Temporarily, until we figure out a more premanent fix
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
      } + labels,
      annotations: {
        summary: summary,
      },
    },
  ],
};

local makeUserPodUnschedulableAlert = function(
  name,
  summary,
  labels={},
                                      ) {
  name: name,
  rules: [
    {
      alert: name,
      expr: |||
        # This alert fires when a user pod is unschedulable for more than 5 minutes.
        # We use kube_pod_status_unschedulable to detect unschedulable pods.
        count(
          kube_pod_status_unschedulable{pod=~'jupyter-.*'} == 1
          and (time() - kube_pod_created > 300)
        ) by (namespace, pod) > 0
      |||,
      'for': '3m',
      labels: {
        cluster: cluster_name,
      } + labels,
      annotations: {
        summary: summary,
      },
    },
  ],
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
            // an alert is for. We don't specify "cluster" here because each alertmanager
            // only handles one cluster
            'alertname',
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
          ],
        },
      },
    },
    serverFiles: {
      'alerting_rules.yml': {
        groups: [
          makePVCApproachingFullAlert(
            'HomeDirectoryDiskApproachingFull',
            'Home Directory Disk about to be full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
            'home-nfs',
          ),
          makePVCApproachingFullAlert(
            'HubDatabaseDiskApproachingFull',
            'Hub Database Disk about to be full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
            'hub-db-dir',
          ),
          makePVCApproachingFullAlert(
            'PrometheusDiskApproachingFull',
            'Prometheus Disk about to be full: cluster:%s' % [cluster_name],
            'support-prometheus-server',
          ),
          makePodRestartAlert(
            'GroupsExporterPodRestarted',
            'jupyterhub-groups-exporter pod has restarted on %s:{{ $labels.namespace }}' % [cluster_name],
            'groups-exporter',
          ),
          makeUserPodUnschedulableAlert(
            'UserPodUnschedulable',
            'The user pod {{ $labels.pod }} is unschedulable on cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
          ),
          diskIOApproachingSaturation,
        ],
      },
    },
  },
}
