#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local prometheus = grafonnet.query.prometheus;

local common = import './common.libsonnet';

local memoryUsage =
  common.tsOptions
  + ts.new('Memory Usage')
  + ts.panelOptions.withDescription(
    |||
      Per group memory usage

      Requires https://github.com/2i2c-org/jupyterhub-groups-exporter to
      be set up.
    |||
  )
  + ts.standardOptions.withUnit('bytes')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          container_memory_working_set_bytes{name!="", pod=~"jupyter-.*", namespace=~"$hub_name"}
            * on (namespace, pod) group_left(annotation_hub_jupyter_org_username, usergroup)
            group(
                kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~".*", pod=~"jupyter-.*"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
            * on (namespace, annotation_hub_jupyter_org_username) group_left(usergroup)
            group(
              label_replace(jupyterhub_user_group_info{namespace=~"$hub_name", username=~".*", usergroup=~"$user_group"},
                "annotation_hub_jupyter_org_username", "$1", "username", "(.+)")
            ) by (annotation_hub_jupyter_org_username, usergroup, namespace)
        ) by (usergroup, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ usergroup }} - ({{ namespace }})'),
  ]);


local cpuUsage =
  common.tsOptions
  + ts.new('CPU Usage')
  + ts.panelOptions.withDescription(
    |||
      Per group CPU usage

      Requires https://github.com/2i2c-org/jupyterhub-groups-exporter to
      be set up.
    |||
  )
  + ts.standardOptions.withUnit('percentunit')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          # exclude name="" because the same container can be reported
          # with both no name and `name=k8s_...`,
          # in which case sum() by (pod) reports double the actual metric
          irate(container_cpu_usage_seconds_total{name!="", pod=~"jupyter-.*"}[5m])
          * on (namespace, pod) group_left(annotation_hub_jupyter_org_username)
          group(
              kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~".*"}
          ) by (pod, namespace, annotation_hub_jupyter_org_username)
          * on (namespace, annotation_hub_jupyter_org_username) group_left(usergroup)
          group(
            label_replace(jupyterhub_user_group_info{namespace=~"$hub_name", username=~".*", usergroup=~"$user_group"},
              "annotation_hub_jupyter_org_username", "$1", "username", "(.+)")
          ) by (annotation_hub_jupyter_org_username, usergroup, namespace)
        ) by (usergroup, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ usergroup }} - ({{ namespace }})'),
  ]);

local homedirSharedUsage =
  common.tsOptions
  + ts.new('Home Directory Usage (on shared home directories)')
  + ts.panelOptions.withDescription(
    |||
      Per group home directory size, when using a shared home directory.

      Requires https://github.com/yuvipanda/prometheus-dirsize-exporter and https://github.com/2i2c-org/jupyterhub-groups-exporter to
      be set up.
    |||
  )
  + ts.standardOptions.withUnit('bytes')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          max(
            dirsize_total_size_bytes{namespace=~"$hub_name"}
          ) by (namespace, directory)
          * on (namespace, directory) group_left(usergroup)
          group(
            label_replace(
              jupyterhub_user_group_info{namespace=~"$hub_name", username_escaped=~".*", usergroup=~"$user_group"},
              "directory", "$1", "username_escaped", "(.+)")
          ) by (directory, namespace, usergroup)
        ) by (namespace, usergroup)
      |||
    )
    + prometheus.withLegendFormat('{{ usergroup }} - ({{ namespace }})'),
  ]);

local memoryRequests =
  common.tsOptions
  + ts.new('Memory Requests')
  + ts.panelOptions.withDescription(
    |||
      Per group memory requests

      Requires https://github.com/2i2c-org/jupyterhub-groups-exporter to
      be set up.
    |||
  )
  + ts.standardOptions.withUnit('bytes')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          kube_pod_container_resource_requests{resource="memory", namespace=~"$hub_name", pod=~"jupyter-.*"}  * on (namespace, pod)
          group_left(annotation_hub_jupyter_org_username) group(
            kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~".*"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
          * on (namespace, annotation_hub_jupyter_org_username) group_left(usergroup)
          group(
            label_replace(jupyterhub_user_group_info{namespace=~"$hub_name", username=~".*", usergroup=~"$user_group"},
              "annotation_hub_jupyter_org_username", "$1", "username", "(.+)")
          ) by (annotation_hub_jupyter_org_username, usergroup, namespace)
        ) by (usergroup, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ usergroup }} - ({{ namespace }})'),
  ]);

local cpuRequests =
  common.tsOptions
  + ts.new('CPU Requests')
  + ts.panelOptions.withDescription(
    |||
      Per group CPU requests

      Requires https://github.com/2i2c-org/jupyterhub-groups-exporter to
      be set up.
    |||
  )
  + ts.standardOptions.withUnit('percentunit')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          kube_pod_container_resource_requests{resource="cpu", namespace=~"$hub_name", pod=~"jupyter-.*"} * on (namespace, pod)
          group_left(annotation_hub_jupyter_org_username) group(
            kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~".*"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
          * on (namespace, annotation_hub_jupyter_org_username) group_left(usergroup)
          group(
            label_replace(jupyterhub_user_group_info{namespace=~"$hub_name", username=~".*", usergroup=~"$user_group"},
              "annotation_hub_jupyter_org_username", "$1", "username", "(.+)")
          ) by (annotation_hub_jupyter_org_username, usergroup, namespace)
        ) by (usergroup, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ usergroup }} - ({{ namespace }})'),
  ]);

dashboard.new('User Group Diagnostics Dashboard')
+ dashboard.withTags(['jupyterhub'])
+ dashboard.withUid('group-diagnostics-dashboard')
+ dashboard.withEditable(true)
+ dashboard.withVariables([
  common.variables.prometheus,
  common.variables.hub_name,
  common.variables.user_group,
])
+ dashboard.withPanels(
  grafonnet.util.grid.makeGrid(
    [
      memoryUsage,
      cpuUsage,
      homedirSharedUsage,
      memoryRequests,
      cpuRequests,
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
