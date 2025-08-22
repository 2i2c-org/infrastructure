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

## What to do when a server can not be started

Any time a server startup fails for any reason, we trigger an alert ("Server Startup Failed").

The causes for this can be varied, and it always requires investigation.
Some common causes are:

1. Node was too slow to spin up. This may be transient - test again, and if this works, it's fine.
2. The user may try to bring their own image and that image is not available or buggy in some way. There is not much we can do here.
3. Appropriate nodepools have not been created somehow. Check the autoscaler logs, and examine the pod specification carefully (particularly `affinity` and `nodeSelector`).
4. The requested resources are too big to fit on the node type that was requested. Our resource generation script is designed to guard against this. Check to see if we are actually using the resource generation script here.
5. There is not enough quota in the cloud project for node spin up to happen. Check the cloud console to see if this is the case, and request additional quota.
6. There is a cloud provider outage. Check out their status page.
7. A mysterious 7th option. Form a mental model of our infrastructure, and poke around.

Since the metric we use here is a counter, it will *mostly* not autoresolve - once you have debugged it, you must manually resolve it. It *will* autoresolve if you delete the hub pod though - so watch for that as a false positive.