# Manage alerts configured with Jsonnet

In addition to [](#uptime-checks), we also have a set of alerts that are configured in support deployments using [](#topic/jsonnet).

## Configuration

We use the [Prometheus alert manager](https://prometheus.io/docs/alerting/latest/overview/) to set up alerts that are defined in the `helm-charts/support/values.jsonnet` file.

At the time of writing, we have the following classes of alerts:

1. when a persistent volume claim (PVC) is approaching full capacity
2. when a pod has restarted.

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

## When a pod has restarted

We monitor pod restarts for the following services:

- `jupyterhub-groups-exporter`

If a pod has restarted, it may indicate an issue with the service or its configuration. Check the logs of the pod to identify any errors or issues that may have caused the restart. If necessary, add more error handling to the code, redeploy the service or adjust its configuration to resolve the issue.

Once the pod is stable, ensure that the alert is resolved by checking whether the pod has been running without restarts, e.g. by running the following command:

```bash
$ kubectl -n <namespace> get pod
NAME                                                 READY   STATUS    RESTARTS      AGE
staging-groups-exporter-deployment-9b4c6749c-sgfcc   1/1     Running   0   10m
```

If you have taken the above actions and the issue persists, then open a GitHub issue capturing the details of the problem for consideration by the wider 2i2c team. See [](#uptime-checks) on how to snooze an alert in the meantime.
