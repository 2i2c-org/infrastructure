#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import 'github.com/grafana/grafonnet/gen/grafonnet-v11.1.0/main.libsonnet';
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local var = grafonnet.dashboard.variable;

local common = import './common.libsonnet';


local totalDailyCosts =
  ts.new('Total daily costs')
  + ts.panelOptions.withDescription(
    |||
      Total daily costs
    |||
  )
  + ts.standardOptions.withMin(20)
  + ts.options.withTooltip({ mode: 'single' })
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
    "showLegend": true
   })
  + ts.fieldConfig.defaults.custom.withLineInterpolation('stepAfter')
  + ts.fieldConfig.defaults.custom.withFillOpacity(10)
  + ts.standardOptions.withUnit('currencyUSD')
  + ts.queryOptions.withTargets([
    {
      datasource: {
        type: 'yesoreyeram-infinity-datasource',
        uid: '${infinity_datasource}',
      },
      url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs?from=${__from:date}&to=${__to:date}",
      format: "table",
      refId: "A",
      columns: [
        {selector: "cost", text: "Cost", type: "number", unit: "currencyUSD"},
        {selector: "date", text: "Date", type: "timestamp"}
      ],
      parser: "backend",
      type: "json",
      source: "url",
      url_options: {
        "method": "GET",
        "data": "",
      },
    }
  ]);


local totalDailyCostsPerHub =
  ts.new('Total daily costs per hub')
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per hub
    |||
  )
  + ts.options.withTooltip({ mode: 'single', sort: "none" })
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
    "showLegend": true,
    "sortBy": "Min (above zero)",
    "sortDesc": true
   })
  + ts.fieldConfig.defaults.custom.withLineInterpolation('stepAfter')
  + ts.fieldConfig.defaults.custom.withFillOpacity(10)
  + ts.fieldConfig.defaults.custom.withStacking("none")
  + ts.standardOptions.color.withMode("palette-classic")
  + ts.standardOptions.thresholds.withMode("absolute")
  + ts.standardOptions.thresholds.withSteps([
    {color: "green", value: null},
    {color: "red", value: 80}
  ])
  + ts.standardOptions.withUnit('currencyUSD')
  + ts.queryOptions.withTargets([
    {
      datasource: {
        type: 'yesoreyeram-infinity-datasource',
        uid: '${infinity_datasource}',
      },
      url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-hub?from=${__from:date}&to=${__to:date}",
      format: "timeseries",
      refId: "A",
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
    }
  ]);


local totalDailyCostsPerComponent =
  ts.new('Total daily costs per component')
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per component
    |||
  )
  + ts.options.withTooltip({ mode: 'single', sort: "none" })
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
    "showLegend": true,
    "sortBy": "Min (above zero)",
    "sortDesc": true
   })
  + ts.fieldConfig.defaults.custom.withLineInterpolation('stepAfter')
  + ts.fieldConfig.defaults.custom.withFillOpacity(10)
  + ts.fieldConfig.defaults.custom.withStacking("none")
  + ts.standardOptions.color.withMode("palette-classic")
  + ts.standardOptions.thresholds.withMode("absolute")
  + ts.standardOptions.thresholds.withSteps([
    {color: "green", value: null},
    {color: "red", value: 80}
  ])
  + ts.standardOptions.withUnit('currencyUSD')
  + ts.queryOptions.withTargets([
    {
      datasource: {
        type: 'yesoreyeram-infinity-datasource',
        uid: '${infinity_datasource}',
      },
      url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}",
      format: "timeseries",
      refId: "A",
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
    }
  ]);


local totalDailyCostsPerComponentAndHub =
  ts.new('Total daily costs per component, for ${hub}')
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per component, for ${hub}
    |||
  )
  + ts.panelOptions.withRepeat('hub')
  + ts.panelOptions.withMaxPerRow(2)
  + ts.options.withTooltip({ mode: 'single', sort: "none" })
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
    "showLegend": true,
    "sortBy": "Min (above zero)",
    "sortDesc": true
   })
  + ts.fieldConfig.defaults.custom.withLineInterpolation('stepAfter')
  + ts.fieldConfig.defaults.custom.withFillOpacity(10)
  + ts.fieldConfig.defaults.custom.withStacking("none")
  + ts.standardOptions.color.withMode("palette-classic")
  + ts.standardOptions.thresholds.withMode("absolute")
  + ts.standardOptions.thresholds.withSteps([
    {color: "green", value: null},
    {color: "red", value: 80}
  ])
  + ts.standardOptions.withUnit('currencyUSD')
  + ts.queryOptions.withTargets([
    {
      datasource: {
        type: 'yesoreyeram-infinity-datasource',
        uid: '${infinity_datasource}',
      },
      url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}&hub=${hub}",
      format: "timeseries",
      refId: "A",
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
    }
  ]);


dashboard.new('Cloud cost attribution')
+ dashboard.withUid('cloud-cost-attribution')
+ dashboard.withEditable(true)
+ dashboard.time.withFrom('now-30d')
+ dashboard.withVariables([
    common.variables.hub,
    common.variables.infinity_datasource,
  ])
+ dashboard.withPanels(
  grafonnet.util.grid.makeGrid(
    [
      totalDailyCosts,
      totalDailyCostsPerHub,
      totalDailyCostsPerComponent,
      totalDailyCostsPerComponentAndHub
    ],
    panelWidth=24,
    panelHeight=12,
  )
)
