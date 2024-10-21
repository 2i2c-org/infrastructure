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
        }
  ]);


// grafonnet ref: https://grafana.github.io/grafonnet/API/dashboard/index.html
//
// A dashboard description can be provided, but isn't used much it seems, due to
// that we aren't providing one atm.
// See https://community.grafana.com/t/dashboard-description-is-it-used-anywhere/53273.
//
dashboard.new("Cloud cost attribution")
+ dashboard.withUid("cloud-cost-aws")
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
