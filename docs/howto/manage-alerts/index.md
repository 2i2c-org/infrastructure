# Manage alerts configured with Jsonnet

In addition to [](#uptime-checks), we also have a set of alerts that are configured in support deployments using [](#topic/jsonnet).

## What to do when an alert fires based on its type and severity
When an alert fires a person should decide how to handle it based on the type of alert and its severity.
Below are some guidelines on how to handle the different types of alerts we have configured.

### Severity and timeline

When an alert fires, it will create an incident in PagerDuty and notify the `#pagerduty-notifications` channel on the 2i2c Slack.
Also, each  alert setup with Jsonnet has a severity level that can be one of:

- `take immediate action`
- `same day action needed`
- `action needed this week`
- `to be planned in sprint planning`

This severity level is what determines how quickly you should respond to the alert.

### What to do when a PVC is approaching full capacity

We monitor the capacity of the following volumes:

- home directories
- hub database
- prometheus database

The alert is triggered when the volume has less than 10% of free space remaining.

To resolve the alert, follow the guidance below

- [](../../howto/filesystem-management/increase-disk-size.md)
- To be documented, see [GH issue](https://github.com/2i2c-org/infrastructure/issues/6187)
- [](../../sre-guide/prometheus-disk-resize.md)

### What to do when a pod has restarted

We monitor pod restarts for the following services:

- `jupyterhub-groups-exporter`

If a pod has restarted, it may indicate an issue with the service or its configuration. Check the logs of the pod to identify any errors or issues that may have caused the restart. If necessary, add more error handling to the code, redeploy the service or adjust its configuration to resolve the issue.

Once the pod is stable, ensure that the alert is resolved by checking whether the pod has been running without restarts, e.g. by running the following command:

```bash
$ kubectl -n <namespace> get pod
NAME                                                 READY   STATUS    RESTARTS      AGE
staging-groups-exporter-deployment-9b4c6749c-sgfcc   1/1     Running   0   10m
```

If you have taken the above actions and the issue persists, then open a GitHub issue capturing the details of the problem for consideration by the wider 2i2c team.

## What do do when a user pod couldn't be scheduled for more than 10 minutes

This alert is triggered when a user pod has been in an unschedulable state for more than 10 minutes based on the value of [`kube_pod_status_unschedulable`](https://docs.cloudera.com/management-console/1.5.4/monitoring-metrics/topics/cdppvc_ds_kube_pod_status_unschedulable_trics.html).

This can happen when there are insufficient resources available in the cluster to schedule the pod, or there are issues with taints and tolerations.

Because a user pod usually gets deleted after it failed to get scheduled and started after 10 minutes and the metric would not be available after that, this alert will not self-resolve once the condition is not true anymore and instead requires manual ticking the `Resolve` button after the cause has been addressed.

If it's just a one-off incident, for one user due to a slow node spawn, resolve the manually and keep an eye of any other similar recurrences.
If the issue persists and can't get to the bottom of it, then open a GitHub issue capturing the details of the problem for consideration by the wider 2i2c team.
