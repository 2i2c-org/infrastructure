local cluster = std.parseYaml(importstr 'cluster.yaml');
local cluster_name = cluster.name;

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
          {
            name: 'home directory full on %s' % [cluster_name],
            rules: [
              {
                alert: 'HomeDirectoryApproachingFull',
                expr: "node_filesystem_avail_bytes{mountpoint='/shared-volume', component='shared-volume-metrics'} / node_filesystem_size_bytes{mountpoint='/shared-volume', component='shared-volume-metrics'} < 0.1",
                'for': '15m',
                labels: {
                  severity: 'critical',
                  channel: 'pagerduty',
                  cluster: cluster_name,
                },
                annotations: {
                  summary: 'Home Directory about to be full: cluster:%s hub:{{ $labels.namespace }}' % [cluster_name],
                },
              },
            ],
          },
        ],
      },
    },
  },
}
