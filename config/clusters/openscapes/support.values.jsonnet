local cluster = "openscapes";
local hubs = ["staging", "workshop", "prod"];

{
  "prometheus": {
    "alertmanager": {
      "enabled": true,
      "config": {
        "route": {
          "group_wait": "10s",
          "group_interval": "5m",
          "receiver": "pagerduty",
          "repeat_interval": "3h",
          "routes": [
            {
              "receiver": "pagerduty",
              "match": {
                "channel": "pagerduty",
                "cluster": cluster,
                "namespace": hub
              }
            } for hub in hubs
          ]
        }
      }
    }
  }
}