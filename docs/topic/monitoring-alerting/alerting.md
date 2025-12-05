# Alerting
We have a few alerts configured to notify us when things go wrong and we use PagerDuty to manage them.

## How to manage alerts

```{important}
[](howto:alerts) has lots of useful howto guides about how to manage this type of alerts that we have setup.
```

## Severity levels
When an alert threshold is crossed, an automatic notification is sent to PagerDuty and the `#pagerduty-notifications` channel on the 2i2c Slack.

Each [alert setup with Jsonnet](alerting:jsonnet-alerts) has a severity level set through the *.jsonnet configuration file. The severity levels are:

- `take immediate action`
- `same day action needed`
- `action needed this week`
- `to be planned in sprint planning`

This level is what determines how quickly you should respond to the alert and translates into the priority of the incident created in PagerDuty. It does this by running an [Event Orchestration](https://support.pagerduty.com/main/docs/event-orchestration) after an incident is created. This Event Orchestration is what sets a priority based on the severity label.

(alerting:priority-levels)=
## Priority levels
The PagerDuty alerts can have a priority between P1 and P4 or have no priority set at all.

### P1 alerts
- These alerts signal an ongoing community outage! [An outage](https://docs.2i2c.org/admin/reliability/outages/#types-of-outages) is a period of time when a hub is unavailable or its critical services are not functioning as expected and impacting two or more of hub users’ activity
- The priority is set by:
   - PagerDuty's Event Orchestration if the alert has a `take immediate action` severity or based on the Service it pertains. (E.g. all [](alerting:hub-health-checks) are P1s)
   - Manually by the engineer

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

### P2 alerts
- These alerts signal that the community is about to be affected if we don't do something asap. E.g. bumping a hub's home directory when it has less than 10% available.
- The priority is set by PagerDuty's Event Orchestration if the alert has a `same day action needed` severity or based on the Service it pertains. (E.g. all [](alerting:hub-health-checks) are P1s)

### P3 alerts
- Correlate with the `action needed this week` severity level
- Community about to be affected if we don't do something soon, but not immediately

### P4 alerts
- Correlate `to be planned in sprint planning` severity level
- Community not necessarily affected on a specific timeline, but we must take some action into the committed column of next sprint


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
