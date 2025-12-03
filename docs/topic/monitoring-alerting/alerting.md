# Alerting
We have a few alerts configured to notify us when things go wrong and we use PagerDuty to manage them.

## How to manage alerts

```{important}
[](howto:alerts) has lots of useful howto guides about how to manage this type of alerts that we have setup.
```

(alerting:jsonnet-alerts)=
## Alerts configured with Jsonnet
There are a set of alerts that are configured in support deployments using [](#topic/jsonnet).

(alerting:configuration)=
### Configuration
We use the [Prometheus alert manager](https://prometheus.io/docs/alerting/latest/overview/) to set up alerts that are defined in the `helm-charts/support/values.jsonnet` file.

At the time of writing, we have the following [alerting rules groups](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/#defining-alerting-rules), and under each group there are one or more alerts:

1. **PVC available capacity**
   For when a persistent volume claim (PVC) is approaching full capacity, with the following alerts:
   - Home Directory Disk 90% full
   - Home Directory Disk 100% full (outage)
   - Hub Database Disk 90% full
   - Prometheus Disk 90% full
2. **Important Pod Restart**
   For when a pod has restarted, with the following alerts:
   - `jupyterhub-groups-exporter` restart
   - `jupyterhub-home-nfs` restart
3. **Server Startup Failure**
   For when a user server has failed to start.
4. **DiskIO saturation**
   For when a disk is approaching IO saturation

Each of these alerts is integrated with a **Pagerduty Service**. And these services can then be grouped under **Pagerduty Business Services** that can be presented on the status page.

```{important}
You can find the existing Services under [Service Directory](https://2i2c-org.pagerduty.com/service-directory) and the existing [Business Services](https://2i2c-org.pagerduty.com/business-services) on [2i2c's Pagerduty page](https://2i2c-org.pagerduty.com).
```

### Severity levels and Priority

When an alert threshold is crossed, an automatic notification is sent to PagerDuty and the `#pagerduty-notifications` channel on the 2i2c Slack.

Also, each  alert setup with Jsonnet has a severity level that is setup through the *.jsonnet configuration file and can be one of:

- `take immediate action`
- `same day action needed`
- `action needed this week`
- `to be planned in sprint planning`

This severity level is what determines how quickly you should respond to the alert and translates into the priority of the incident created in PagerDuty. Also, the level is included in the title of the alert.

It does this by running an [Event Orchestration](https://support.pagerduty.com/main/docs/event-orchestration) after an incident is created.
The Event Orchestration sets a priority based on the severity label of the alert that triggered it.

- `P1`:`take immediate action` (a community currently affected and experiencing an outage)
- `P2`:`same day action needed` (community about to be affected if we don't do something immediately)
- `P3`:`action needed this week` (community about to be affected if we don't do something soon, but not immediately)
- `P4`:`to be planned in sprint planning` (community not necessarily affected on a specific timeline, but we must take some action into the committed column of next sprint)

````{important}
All of the P1 PagerDuty alerts will show up in the 2i2c [status page](https://2i2c-hubs.trust.pagerduty.com/posts/dashboard) and subscribed users will receive updated related to it.
```{figure} ../../images/status-page-pagerduty.png
```
````

````{warning}
If an Alert goes from P1 to another priority number or no number at all, Pagerduty's status page will loose track of it and will forever show up on the status page unless it is manually removed.
```{figure} ../../images/manually-delete-outage.png
```
````

### Important Pagerduty pages to know about
All of the alerts we have configured are managed by [Pagerduty](https://www.pagerduty.com/)
There are some important web pages provided by Pagerduty that are relevant to know about:

1. [2i2c's Pagerduty page](https://2i2c-org.pagerduty.com)
2. [List of incidents](https://2i2c-org.pagerduty.com/incidents)
   This is where **all** incidents can be found
3. [Internal status page](https://2i2c-org.pagerduty.com/status-dashboard)
   This is where **outages** will show up, per business service. Clicking on an incident from this page will link you to the alert.
4. [External status page](https://2i2c-hubs.trust.pagerduty.com/)
   This is where **outages** will show up, per business service to the outside world. This is where people can:
   - subscribe for updates about outages
   - subscribe to get info about maintenance windows that we might post
   - Find out about the uptime of each Business Service.
