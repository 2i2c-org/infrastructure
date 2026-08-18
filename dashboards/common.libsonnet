#!/usr/bin/env -S jsonnet -J ../../vendor
local grafonnet = import '../../vendor/gen/grafonnet-v11.4.0/main.libsonnet';
local var = grafonnet.dashboard.variable;
local ts = grafonnet.panel.timeSeries;
local bc = grafonnet.panel.barChart;
local bg = grafonnet.panel.barGauge;

{
  // grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/variable.html
  variables: {
    prometheus:
      var.datasource.new('PROMETHEUS_DS', 'prometheus')
      + var.datasource.generalOptions.showOnDashboard.withValueOnly()
    ,
    hub:
      var.query.new('hub')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('namespace', 'kube_service_labels{service="hub"}'),
  },
}
