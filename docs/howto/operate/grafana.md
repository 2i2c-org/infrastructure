# Access the Hub Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

The Grafana for each cluster can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the pilot hubs are accessible at `grafana.pilot.2i2c.cloud`. You'll need
a username and password to access each one. Ask one of the 2i2c team members for access.
