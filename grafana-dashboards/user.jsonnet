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
      Per user memory usage
    |||
  )
  + ts.standardOptions.withUnit('bytes')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        sum(
          container_memory_working_set_bytes{name!="", pod=~"jupyter-.*", namespace=~"$hub_name"}
            * on (namespace, pod) group_left(annotation_hub_jupyter_org_username)
            group(
                kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~"$user_name", pod=~"jupyter-.*"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ annotation_hub_jupyter_org_username }} - ({{ namespace }})'),
  ]);


local cpuUsage =
  common.tsOptions
  + ts.new('CPU Usage')
  + ts.panelOptions.withDescription(
    |||
      Per user CPU usage
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
              kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~"$user_name"}
          ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ annotation_hub_jupyter_org_username }} - ({{ namespace }})'),
  ]);

local homedirSharedUsage =
  common.tsOptions
  + ts.new('Home Directory Usage (on shared home directories)')
  + ts.panelOptions.withDescription(
    |||
      Per user home directory size, when using a shared home directory.

      Requires https://github.com/yuvipanda/prometheus-dirsize-exporter to
      be set up.

      Similar to server pod names, user names will be *encoded* here
      using the escapism python library (https://github.com/minrk/escapism).
      You can unencode them with the following python snippet:

      from escapism import unescape
      unescape('<escaped-username>', '-')
    |||
  )
  + ts.standardOptions.withUnit('bytes')
  + ts.queryOptions.withTargets([
    prometheus.new(
      '$PROMETHEUS_DS',
      |||
        max(
          dirsize_total_size_bytes{namespace=~"$hub_name"}
          * on (namespace, directory) group_left(username)
          group(
            label_replace(
              jupyterhub_user_group_info{namespace=~"$hub_name", username_escaped=~".*"},
                "directory", "$1", "username_escaped", "(.+)")
          ) by (directory, namespace, username)
        ) by (namespace, username)
      |||
    )
    + prometheus.withLegendFormat('{{ username }} - ({{ namespace }})'),
  ]);

local memoryRequests =
  common.tsOptions
  + ts.new('Memory Requests')
  + ts.panelOptions.withDescription(
    |||
      Per-user memory requests
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
            kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~"$user_name"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ annotation_hub_jupyter_org_username }} - ({{ namespace }})'),
  ]);

local cpuRequests =
  common.tsOptions
  + ts.new('CPU Requests')
  + ts.panelOptions.withDescription(
    |||
      Per user CPU requests
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
            kube_pod_annotations{namespace=~"$hub_name", annotation_hub_jupyter_org_username=~"$user_name"}
            ) by (pod, namespace, annotation_hub_jupyter_org_username)
        ) by (annotation_hub_jupyter_org_username, namespace)
      |||
    )
    + prometheus.withLegendFormat('{{ annotation_hub_jupyter_org_username }} - ({{ namespace }})'),
  ]);

dashboard.new('User Diagnostics Dashboard')
+ dashboard.withTags(['jupyterhub'])
+ dashboard.withUid('user-diagnostics-dashboard')
+ dashboard.withEditable(true)
+ dashboard.withVariables([
  common.variables.prometheus,
  common.variables.hub_name,
  common.variables.user_name,
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
