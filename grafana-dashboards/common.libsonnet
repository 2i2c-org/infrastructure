local grafonnet = import 'grafonnet/main.libsonnet';
local var = grafonnet.dashboard.variable;
local ts = grafonnet.panel.timeSeries;
local bc = grafonnet.panel.barChart;
local bg = grafonnet.panel.barGauge;

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
            root_selector: '$append($filter($, function($v) {$v != "support" and $v != "binder"}) , "all")',
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
      + var.query.generalOptions.withCurrent('all')
      + var.query.selectionOptions.withIncludeAll(value=false)
      + var.query.selectionOptions.withMulti(value=true)
      + var.query.refresh.onTime(),
    component:
      var.query.new(
        'component',
        {
          query: '',
          queryType: 'infinity',
          infinityQuery: {
            format: 'table',
            parser: 'backend',
            refId: 'variable',
            source: 'url',
            type: 'json',
            url: 'http://jupyterhub-cost-monitoring.support.svc.cluster.local/component-names?from=${__from:date}&to=${__to:date}',
            url_options: {
              data: '',
              method: 'GET',
            },
          },
        },
      )
      + var.query.withDatasourceFromVariable(self.infinity_datasource)
      + var.query.generalOptions.withCurrent({
        text: [
          'compute',
          'home storage',
        ],
        value: [
          'compute',
          'home storage',
        ],
      })
      + var.query.selectionOptions.withIncludeAll(value=false)
      + var.query.selectionOptions.withMulti(value=true)
      + var.query.refresh.onTime(),
  },

  // grafonnet ref: https://grafana.github.io/grafonnet/API/panel/timeSeries/index.html#obj-queryoptions
  queryDailyTarget: {
    datasource: {
      type: 'yesoreyeram-infinity-datasource',
      uid: '${infinity_datasource}',
    },
    columns: [
      { selector: 'date', text: 'Date', type: 'timestamp' },
      { selector: 'name', text: 'Name', type: 'string' },
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

  queryHubTarget: {
    datasource: {
      type: 'yesoreyeram-infinity-datasource',
      uid: '${infinity_datasource}',
    },
    columns: [
      { selector: 'date', text: 'Date', type: 'timestamp' },
      { selector: 'cost', text: 'Cost', type: 'number' },
      { selector: 'name', text: 'Hub', type: 'string' },
    ],
    parser: 'backend',
    type: 'json',
    source: 'url',
    url_options: {
      method: 'GET',
      data: '',
    },
    format: 'table',
    refId: 'A',
  },

  queryComponentTarget: {
    datasource: {
      type: 'yesoreyeram-infinity-datasource',
      uid: '${infinity_datasource}',
    },
    columns: [
      { selector: 'date', text: 'Date', type: 'timestamp' },
      { selector: 'cost', text: 'Cost', type: 'number' },
      { selector: 'component', text: 'Component', type: 'string' },
    ],
    parser: 'backend',
    type: 'json',
    source: 'url',
    url_options: {
      method: 'GET',
      data: '',
    },
    format: 'table',
    refId: 'A',
  },

  queryUsersTarget: {
    datasource: {
      type: 'yesoreyeram-infinity-datasource',
      uid: '${infinity_datasource}',
    },
    columns: [
      { selector: 'date', text: 'Date', type: 'timestamp' },
      { selector: 'value', text: 'Cost', type: 'number' },
      { selector: 'user', text: 'User', type: 'string' },
      { selector: 'component', text: 'Component', type: 'string' },
    ],
    parser: 'backend',
    type: 'json',
    source: 'url',
    url_options: {
      method: 'GET',
      data: '',
    },
    format: 'table',
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
    bc.standardOptions.withMin(0)
    + bc.standardOptions.withDecimals(2)
    + bc.standardOptions.withUnit('currencyUSD')
    + bc.options.withBarWidth(0.9)
    + bc.options.withFullHighlight(false)
    + bc.options.withLegend({ calcs: ['sum'] })
    + bc.options.legend.withDisplayMode('table')
    + bc.options.legend.withPlacement('right')
    + bc.options.legend.withSortBy('Total')
    + bc.options.legend.withSortDesc(true)
    + bc.options.tooltip.withMode('multi')
    + bc.options.tooltip.withSort('desc')
    + bc.options.withXTickLabelSpacing(100)
    + bc.options.withShowValue('never')
    + bc.options.withStacking('normal')
    + bc.queryOptions.withTransformations([
      bc.queryOptions.transformation.withId('formatTime')
      + bc.queryOptions.transformation.withOptions({
        outputFormat: 'MMM DD',
        timeField: 'Date',
        useTimezone: true,
      }),
      bc.queryOptions.transformation.withId('groupBy')
      + bc.queryOptions.transformation.withOptions({
        fields: {
          Component: {
            aggregations: [],
          },
          Cost: {
            aggregations: [
              'sum',
            ],
            operation: 'aggregate',
          },
          Date: {
            aggregations: [],
            operation: 'groupby',
          },
          User: {
            aggregations: [],
            operation: 'groupby',
          },
        },
      }),
      bc.queryOptions.transformation.withId('groupingToMatrix')
      + bc.queryOptions.transformation.withOptions({
        columnField: 'User',
        emptyValue: 'zero',
        rowField: 'Date',
        valueField: 'Cost (sum)',
      }),
    ]),

  bgOptions:
    bg.options.withDisplayMode('basic')
    + bg.options.withOrientation('horizontal')
    + bg.options.withValueMode('text')
    + bg.standardOptions.withMin(0)
    + bg.standardOptions.withDecimals(2)
    + bg.standardOptions.withUnit('currencyUSD'),
}
