(howto:alerts)=
# Manage alerts

In addition to [](#uptime-checks), we also have a set of alerts that are configured in support deployments using [](#topic/jsonnet).
More about these alerts at [](alerting:jsonnet-alerts)

## What to do when an alert fires based on its type and severity
When an alert fires a person should decide how to handle it based on the type of alert and its severity.
The general steps to take for any alert are:

1. Validate/invalidate as quickly as possible if we are dealing with an outage
2. If an outage, then add the P1 priority to the PD incident and follow the incident process
3. If not an outage, then time-box yourself to 30 min and either debug or fix it if you know how
4. After 30min, use your judgement to decide if you need to create a follow-up issue to investigate further. It might be that you believe that extra time invested won't bring any light into the root cause. This is ok. Just leave a note in PD.
5. Close the alert in PD and link to the issue if you created one

Below are some guidelines on how to handle the different types of alerts we have configured.

### Severity and timeline

When an alert fires, it will create an incident in PagerDuty and notify the `#pagerduty-notifications` channel on the 2i2c Slack.
Each  alert setup with Jsonnet has a severity level that can be one of:

- `take immediate action`
- `same day action needed`
- `action needed this week`
- `to be planned in sprint planning`

This severity level, together with the priority levels described in [](alerting:priority-levels) is what determines how quickly you should respond to the alert.

### What to do for alerts about JupyterHub not being available

These alerts are outages and have a P1 priority set by default.
To resolve this alert:
- check if another engineer is doing any work/testing/decommissioning of the hub
- if they are, then resolve the alert in PD and remove its P1 priority (in this order)
- if they're not, then
  - validate if the hub is indeed not available
  - follow the incident response process

### What to do for alerts on PVC capacity

We monitor the capacity of the following volumes:
- home directories
- hub database
- prometheus database

There are two alert types that are triggered based a capacity threshold:

- **A P2 alert** at 10%

  It is triggered when the volume has less than 10% of free space remaining and is assigned a `same day action needed`, hence a P2 priority.
  To resolve the alert, follow the guidance below:

  1. Ack the alert in PD
  2. [](../../howto/filesystem-management/increase-disk-size.md)
  3. To be documented, see [GH issue](https://github.com/2i2c-org/infrastructure/issues/6187)
  4. [](../../sre-guide/prometheus-disk-resize.md)

- **A P1 at 0%**

  - It is triggered when the volumes doesn't have any capacity left.
  - If we respond in time to the P2 alert, this one should never trigger.
  - This alert is assigned a `take immediate action` severity level and a P1 priority, hence it is an **outage**.
  - To resolve the alert, use the guides from the bullet above.

### What to do for alerts on pod restarts

We monitor pod restarts for the following services:

- `jupyterhub-groups-exporter`
- `jupyterhub-home-nfs`

If a pod has restarted, it may indicate an issue with the service or its configuration.
To resolve the alert:
  1. Ack the alert in PD
  2. Check if the pod is running or is restarting infinitely
  3. Check the logs of the pod to identify any errors or issues that may have caused the restart
    - If the pod is stable and not restarting anymore, see if the logs present anything useful enough to open a tracking issue. And if not, mark the alert as resolved.
    - If the pod is still restarting, try getting it in a stable state by redeploying it or adjust its configuration to resolve the issue.
  4. If you have taken the above actions and the issue persists, then
    - Open a GitHub issue capturing the details of the problem for consideration by the wider 2i2c team.
    - Setup a Priority number on the alert

### What to do for alerts on server startup failures

Any time two consecutive spawns fail in a 30m time window, we trigger an alert. This alert doesn't have a severity lever or a priority level set on it by default because it can be anything. This is why is best to investigate these ASAP.

The causes for this can be varied, and it always requires investigation. Some common causes are:
1. Node was too slow to spin up. This may be transient - test again, and if this works, it's fine.
2. The user may try to bring their own image and that image is not available or buggy in some way. There is not much we can do here.
3. Appropriate nodepools have not been created somehow. Check the autoscaler logs, and examine the pod specification carefully (particularly `affinity` and `nodeSelector`).
4. The requested resources are too big to fit on the node type that was requested. Our resource generation script is designed to guard against this. Check to see if we are actually using the resource generation script here.
5. There is not enough quota in the cloud project for node spin up to happen. Check the cloud console to see if this is the case, and request additional quota.
6. There is a cloud provider outage. Check out their status page.
7. A mysterious 7th option. Form a mental model of our infrastructure, and poke around. If you find any useful info, 

To resolve the alert:
1. Check if you can spawn a server on that cluster and hub. If not, then is most likely an outage an you must set the P1 priority on this alert and follow the incident response process for outages.
2. If you can spawn a server, then this is most likely not an outage. But check the list of possible causes above and find the one that matches what you're seeing in the logs.
  - If logs are not available or not proving any useful info, then you can manually resolve the alert in PD as a mystery. It will likely come back if there's an underlying issue and a pair of eyes will be available to investigate.
  - If the logs seem suspicious but you cannot put your finger on the issue, then open a tracking GitHub issue to be discussed with the rest of the engineering team.


## How to get useful information about an alert

Each automatic alert will have a title which is formed using the alert name and various labels considered important.

Example: `[FIRING:1] home-nfs has 10% of space left openscapes prod (same day action needed)`.

- The `FIRING:n` part tracks how many times the alert has been triggered. But because we are not yet grouping alerts, it will always be 1, so it can be ignored.
- `<disk name> has <limit>% of space left` this is the alert name and it has info about which disk the alert is about and how much space left it has
- `<cluster-name> <hub-name>` these are labels that provide info about the cluster and hub for which the alert has triggered for
- `same day action needed` the severity of the alert, which set the timeline when this alert should be handled 

Also, clicking on an alert in PagerDuty, gets you all the metadata associated with it, where you can find extra info, like the summary.

## How to add a new alert

1. To add a new alert, you'll have to add it to `/helm-charts/support/values.jsonnet` first after checking out [](#topic/jsonnet).
2. Then, if this is an alert that doesn't pertain to any of the existing alerting groups as defined in [](alerting:configuration), you'll have to:
  - create a new group
  - create a new Service in Pagerduty for this groups
  - get the integration key of this service and store it encrypted under a new Pagerduty receiver
  - write a matcher rule in Alert Manager that will link this group to this new receiver
3. Test i
4. If you know what the outage condition for this new group is, create a new Orchestration rule for it, so that outage alerts are automatically assigned P1 and shown in the status page