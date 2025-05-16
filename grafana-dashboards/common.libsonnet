local grafonnet = import "grafonnet/main.libsonnet";
local var = grafonnet.dashboard.variable;
local ts = grafonnet.panel.timeSeries;

{
  // grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/variable.html
  variables: {
    infinity_datasource:
      var.datasource.new("infinity_datasource", "yesoreyeram-infinity-datasource")
      + var.datasource.generalOptions.showOnDashboard.withNothing()
    ,
    prometheus:
      var.datasource.new('PROMETHEUS_DS', 'prometheus')
      + var.datasource.generalOptions.showOnDashboard.withValueOnly()
    ,
    // Limit namespaces to those that run a hub service    
    hub:
      var.query.new(
        "hub",
        {
          query: "",
          queryType: "infinity",
          infinityQuery: {
            format: "table",
            parser: "backend",
            refId: "variable",
            source: "url",
            type: "json",
            url: "http://aws-ce-grafana-backend.support.svc.cluster.local/hub-names?from=${__from:date}&to=${__to:date}",
            url_options: {
              data: "",
              method: "GET"
            },
          },
        },
      )
      + var.query.withDatasourceFromVariable(self.infinity_datasource)
      + var.query.selectionOptions.withIncludeAll(value=true)
      + var.query.generalOptions.showOnDashboard.withNothing()
      + var.query.refresh.onTime()
    ,
    hub_name:
      var.query.new('hub_name')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')      
      + var.query.queryTypes.withLabelValues('namespace', 'kube_service_labels{service="hub"}')
    ,
    // Queries should use the 'instance' label when querying metrics that
    // come from collectors present on each node - such as node_exporter or
    // container_ metrics, and use the 'node' label when querying metrics
    // that come from collectors that are present once per cluster, like
    // kube_state_metrics.
    instance:
      var.query.new('instance')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('node', 'kube_node_info'),
    namespace:
      var.query.new('namespace')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('namespace', 'kube_pod_labels')
    ,
    user_group:
      var.query.new('user_group')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('usergroup', 'jupyterhub_user_group_info')
    ,    
    user_name:
      var.query.new('user_name')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('annotation_hub_jupyter_org_username', 'kube_pod_annotations{ namespace=~"$hub"}')
    ,
    user_pod:
      var.query.new('user_pod')
      + var.query.withDatasourceFromVariable(self.prometheus)
      + var.query.selectionOptions.withMulti()
      + var.query.selectionOptions.withIncludeAll(value=true, customAllValue='.*')
      + var.query.queryTypes.withLabelValues('pod', 'kube_pod_labels{label_app="jupyterhub", label_component="singleuser-server", namespace=~"$hub"}')
    ,
  },

  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html#obj-queryoptions
  queryTarget: {
    datasource: {
      type: "yesoreyeram-infinity-datasource",
      uid: "${infinity_datasource}",
    },
    columns: [
      {selector: "date", text: "Date", type: "timestamp"},
      {selector: "name", text: "Name", type: "string"},
      {selector: "cost", text: "Cost", type: "number"}
    ],
    parser: "backend",
    type: "json",
    source: "url",
    url_options: {
      "method": "GET",
      "data": "",
    },
    format: "timeseries",
    refId: "A",
  },

  // grafana ref:   https://grafana.com/docs/grafana/v11.1/panels-visualizations/visualizations/time-series/
  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html
  tsOptions:
    ts.standardOptions.withMin(0)
    + ts.options.withTooltip({ mode: "multi", sort: "desc" })
    + ts.fieldConfig.defaults.custom.withLineInterpolation("stepAfter")
    + ts.fieldConfig.defaults.custom.withFillOpacity(10)
    + ts.standardOptions.withUnit("currencyUSD")
    + ts.standardOptions.withDecimals(2)
    + ts.options.withLegend({
      "calcs": [
        "count",
        "min",
        "mean",
        "max",
        "sum"
      ],
      "displayMode": "table",
      "placement": "bottom",
      "sortBy": "Total",
      "sortDesc": true,
    })
  ,
}
