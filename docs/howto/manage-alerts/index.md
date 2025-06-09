# Managing alerts configured with Jsonnet

In addition to [](#uptime-checks), we also have a set of alerts that are configured in support deployments using [](#topic/jsonnet).

## Configuration

We use the [Prometheus alert manager](https://prometheus.io/docs/alerting/latest/overview/) to set up alerts that are defined in the `helm-charts/support/values.jsonnet` file.

At the time of writing, we have the following classes of alerts:

1. when a persistent volume claim (PVC) is approaching full capacity
2. when a pod has restarted in the last hour.

When an alert threshold is crossed, an automatic notification is sent to PagerDuty and the `#pagerduty-notifications` channel on the 2i2c Slack.

## When a PVC is approaching full capacity

We monitor the capacity of the following volumes:

- home directories
- hub database
- prometheus database

The alert is triggered when the volume is more than 90% full.

To resolve the alert, follow the guidance below

- [](../../howto/filesystem-management/increase-disk-size.md)
- **TODO: add instructions for hub database**
- [](../../sre-guide/prometheus-disk-resize.md)

## When a pod has restarted in the last hour

We monitor pod restarts for the following services:

- `jupyterhub-groups-exporter`

If a pod has restarted in the last hour, it may indicate an issue with the service or its configuration. Check the logs of the pod to identify any errors or issues that may have caused the restart. If necessary, redeploy the service or adjust its configuration to resolve the issue.

If you have taken the above actions and the issue persists, then open a GitHub issue capturing the details of the problem for consideration by the wider 2i2c team.
