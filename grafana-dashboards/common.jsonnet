local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local var = grafonnet.dashboard.variable;

{
  // grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/variable.html
  variables: {
    datasource:
      var.datasource.new('datasource', 'yesoreyeram-infinity-datasource')
      + var.datasource.generalOptions.showOnDashboard.withNothing()
    ,
    newhub:
      var.query.new('hub')
      + var.query.withDatasourceFromVariable(self.datasource)
      + var.query.selectionOptions.withIncludeAll(value=true)
    ,
  },
}
