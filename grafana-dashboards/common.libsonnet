local grafonnet = import 'grafonnet/main.libsonnet';
local var = grafonnet.dashboard.variable;
local ts = grafonnet.panel.timeSeries;
local bc = grafonnet.panel.barChart;

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
          query: '',
          queryType: 'infinity',
          infinityQuery: {
            format: 'table',
            parser: 'backend',
            refId: 'variable',
            source: 'url',
            type: 'json',
            url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/hub-names?from=${__from:date}&to=${__to:date}',
            url_options: {
              data: '',
              method: 'GET',
            },
          },
        },
      )
      + var.query.withDatasourceFromVariable(self.infinity_datasource)
      + var.query.selectionOptions.withIncludeAll(value=true)
      + var.query.generalOptions.showOnDashboard.withNothing()
      + var.query.refresh.onTime(),
  },

  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html#obj-queryoptions
  queryTarget: {
    datasource: {
      type: 'yesoreyeram-infinity-datasource',
      uid: '${infinity_datasource}',
    },
    columns: [
      { selector: 'date', text: 'Date', type: 'timestamp' },
      { selector: 'component', text: 'Component', type: 'string' },
      { selector: 'cost', text: 'Cost', type: 'number' },
    ],
    parser: 'backend',
    type: 'json',
    source: 'url',
    url_options: {
      method: 'GET',
      data: '',
    },
    format: 'timeseries',
    refId: 'A',
  },

  // grafana ref:   https://grafana.com/docs/grafana/v11.1/panels-visualizations/visualizations/time-series/
  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html
  tsOptions:
    ts.standardOptions.withMin(0)
    + ts.options.withTooltip({ mode: 'multi', sort: 'desc' })
    + ts.fieldConfig.defaults.custom.withLineInterpolation('stepAfter')
    + ts.fieldConfig.defaults.custom.withFillOpacity(10)
    + ts.standardOptions.withUnit('currencyUSD')
    + ts.standardOptions.withDecimals(2)
    + ts.options.withLegend({
      calcs: [
        'count',
        'min',
        'mean',
        'max',
        'sum',
      ],
      displayMode: 'table',
      placement: 'bottom',
      sortBy: 'Total',
      sortDesc: true,
    }),

  bcOptions:
    bc.standardOptions.withMin(0),
}
