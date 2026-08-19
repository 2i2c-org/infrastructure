local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local var = grafonnet.dashboard.variable;
local ts = grafonnet.panel.timeSeries;

{
  // grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/variable.html
  variables: {
    prometheus:
      var.datasource.new('PROMETHEUS_DS', 'prometheus')
      + var.datasource.generalOptions.showOnDashboard.withNothing()
    ,
    hub:
      var.query.new('hub')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('namespace', 'kube_service_labels{service="hub"}'),
    user:
      var.query.new('user')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('username', 'jupyterhub_memory_usage_byte_hours_total'),
  },

  // grafana ref:   https://grafana.com/docs/grafana/v11.1/panels-visualizations/visualizations/time-series/
  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html
  tsOptions:
    ts.standardOptions.withMin(0)
    + ts.fieldConfig.defaults.custom.withLineWidth(2)
    + ts.fieldConfig.defaults.custom.withShowPoints('never'),
}
