local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local var = grafonnet.dashboard.variable;

{
  // grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/variable.html
  variables: {
    infinity_datasource:
      var.datasource.new('infinity_datasource', 'yesoreyeram-infinity-datasource')
      + var.datasource.generalOptions.showOnDashboard.withNothing()
    ,
    hub:
      var.query.new(
        'hub',
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
            }
          },
        }
      )
      + var.query.withDatasourceFromVariable(self.infinity_datasource)
      + var.query.selectionOptions.withIncludeAll(value=true)
      + var.query.generalOptions.showOnDashboard.withNothing()
      + var.query.refresh.onTime()
    ,
  },
}
