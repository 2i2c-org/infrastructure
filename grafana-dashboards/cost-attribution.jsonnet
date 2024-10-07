#!/usr/bin/env -S jsonnet -J ../vendor
local grafonnet = import "grafonnet/main.libsonnet";
local dashboard = grafonnet.dashboard;
local ts = grafonnet.panel.timeSeries;
local var = grafonnet.dashboard.variable;

local common = import "./common.libsonnet";


local totalDailyCosts =
  common.tsOptions
  + ts.new("Total daily costs")
  + ts.panelOptions.withDescription(
    |||
      Total daily costs
    |||
  )
  + ts.queryOptions.withTargets([
      common.queryTarget
      + {
          url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs?from=${__from:date}&to=${__to:date}",
          columns: [
            {selector: "cost", text: "Cost", type: "number"},
            {selector: "date", text: "Date", type: "timestamp"},
          ],
        }
  ]);


local totalDailyCostsPerHub =
  common.tsOptions
  + ts.new("Total daily costs per hub")
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per hub
    |||
  )
  + ts.queryOptions.withTargets([
      common.queryTarget
      + {
          url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-hub?from=${__from:date}&to=${__to:date}",
          columns: [
            {selector: "date", text: "Date", type: "timestamp"},
            {selector: "name", text: "Name", type: "string"},
            {selector: "cost", text: "Cost", type: "number"}
          ],
        }
  ]);


local totalDailyCostsPerComponent =
  common.tsOptions
  + ts.new("Total daily costs per component")
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per component
    |||
  )
  + ts.queryOptions.withTargets([
      common.queryTarget
      + {
          url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}",
          columns: [
            {selector: "date", text: "Date", type: "timestamp"},
            {selector: "name", text: "Name", type: "string"},
            {selector: "cost", text: "Cost", type: "number"}
          ],
        }
  ]);


local totalDailyCostsPerComponentAndHub =
  common.tsOptions
  + ts.new("Total daily costs per component, for ${hub}")
  + ts.panelOptions.withDescription(
    |||
      Total daily costs per component, for ${hub}
    |||
  )
  + ts.panelOptions.withRepeat("hub")
  + ts.panelOptions.withMaxPerRow(2)
  + ts.queryOptions.withTargets([
      common.queryTarget
      + {
          url: "http://aws-ce-grafana-backend.support.svc.cluster.local/total-costs-per-component?from=${__from:date}&to=${__to:date}&hub=${hub}",
          columns: [
            {selector: "date", text: "Date", type: "timestamp"},
            {selector: "name", text: "Name", type: "string"},
            {selector: "cost", text: "Cost", type: "number"}
          ],
        }
  ]);


// grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/index.html
dashboard.new("Cloud cost attribution")
+ dashboard.withUid("cloud-cost-attribution")
+ dashboard.withTimezone("utc")
+ dashboard.withEditable(true)
+ dashboard.time.withFrom("now-30d")
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
