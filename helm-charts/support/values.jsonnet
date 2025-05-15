local cluster_name = std.extVar("2I2C_VARS.CLUSTER_NAME");

local makePVCApproachingFullAlert = function(
  name,
  summary,
  persistentvolumeclaim,
) {
      # Structure is documented in https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
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
            severity: 'critical',
            channel: 'pagerduty',
            cluster: cluster_name,
          },
          annotations: {
            summary: summary
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
          repeat_interval: '3h',
          routes: [
            {
              receiver: 'pagerduty',
              match: {
                channel: 'pagerduty',
              },
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
        ],
      },
    },
  },
}
