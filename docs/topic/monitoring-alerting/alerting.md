# Alerting
We have a few alerts configured to notify us when things go wrong and we use PagerDuty to manage them.

## Paging
We don't have an on-call rotation currently, and nobody is expected to
respond outside working hours. Hence, we don't really currently have paging
alerts.

However, we may temporarily mark some alerts to page specific people during
ongoing incidents that have not been resolved yet. This is usually done
to monitor a temporary fix that may or may not have solved the issue. By
adding a paging alert, we buy ourselves a little peace of mind - as long
as the page is not firing, we are doing ok.

Alerts should have a label named `page` that can be set to the pagerduty username of whoever should be paged for that alert.

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
```{figure} ../../images/manually-remove-outage.png
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

(uptime-checks)=
## Simple HTTPS uptime checks

Ideally, when a hub is down, a machine alerts us - we do not have to wait for a user
to report it to our helpdesk. While we aren't quite there, we currently have very simple
uptime monitoring for all our hubs with free [GCP Uptime Checks](https://cloud.google.com/monitoring/uptime-checks).

### Where are the checks?

Uptime checks are *centralized* - they don't exist in the same project or cloud provider
as the hubs they are checking, but in one centralized GCP project (`two-eye-two-see`). This
has a few advantages:

1. We do not have to implement the same functionality three times (one per cloud provider),
   as we would have to if this were to exist in the same project as the hub.
2. These are all 'black box' external checks, so it does not particularly matter where they
   come from.

You can browse the existing checks [on the GCP Console](https://console.cloud.google.com/monitoring/uptime?project=two-eye-two-see)
as well.

### Cost

Note that as of October 2022 [Google Stackdriver
Pricing](https://cloud.google.com/stackdriver/pricing) the free monthly quota is
1 million executions of uptime checks per project.

| Feature | Price | Free allotment per month | Effective date |
| --- | --- | --- | --- |
| Execution of Monitoring uptime checks| $0.30/1,000 executions| 1 million executions per Google Cloud project|	October 1, 2022 |

### When are notifications triggered?

Our uptime checks are performed every 15 minutes, and we alert if checks have failed for 31 minutes.
This make sure there are at least 2 failed checks before we alert.

We are optimizing for *actionable alerts* that we can completely *trust*,
and prevent any kind of alert fatigue for our engineers.

#### JupyterHub health checks

The JupyterHub *does* get restarted during deployment, and this can cause a few
seconds of downtime - and we do not want to alert in case the uptime check hits
the hub *just* at that moment. We trade-off a few minutes of responsiveness for
trust here. `/hub/health` is the endpoint checked for hubs, and `/health` is checked
for binderhub.

When an alert is triggered, it automatically opens an Incident in the
[Managed JupyterHubs](https://2i2c-org.pagerduty.com/service-directory/PS10YJ3) service
we maintain in PagerDuty. This also notifies the `#pagerduty-notifications` channel on
the 2i2c slack, and kicks off [our incident response process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)

#### Prometheus health checks

Our prometheus instances are protected by auth, so we just check to see if we get a
`401 Unauthorized` response from the prometheus instance.

When an alert is triggered, it automatically opens an Incident in the
[Cluster Prometheus](https://2i2c-org.pagerduty.com/service-directory/P4B7MEA) service
we maintain in PagerDuty. This also notifies the `#pagerduty-notifications` channel on
the 2i2c slack, and kicks off [our incident response process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)


### How are the checks set up?

We use Terraform in the [terraform/uptime-checks](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/uptime-checks)
directory to set up the checks, notifications channel and alerting policies. This allows new
checks to be created *automatically* whenever a new hub or cluster is added, with no manual
steps required.

 Terraform is run in our continuous deployment pipeline on GitHub actions at the
 end of every deployment, using [a GCP
 ServiceAccount](https://console.cloud.google.com/iam-admin/serviceaccounts/details/114061400394069109140?project=two-eye-two-see)
 that was manually created. It has just enough permissions to access the
 terraform state (on GCS), the uptime checks, notification channels and alert
 policies. *Nothing destructive* can happen if this `terraform apply` goes
 wrong, so it is alright to run this without human supervision on GitHub Actions

(uptime-checks:snoozes)=
### How do I snoooze a check?

As the checks are all in GCP they can be created through the [monitoring console](https://console.cloud.google.com/monitoring/alerting?project=two-eye-two-see).

The `alpha` gcloud component also supports setting snoozes from the command line. For further documentation see the [Google Cloud Monitoring docs](https://cloud.google.com/monitoring/alerts/manage-snooze#gcloud-cli) or the [gcloud alpha monitoring snoozes](https://cloud.google.com/sdk/gcloud/reference/alpha/monitoring/snoozes) reference. You may need to add the `alpha` component to your `gcloud` install.


Example CLI use that snoozes staging check for 7 days:

```
HUB=staging
POLICY=$(gcloud alpha monitoring policies list  --filter "displayName ~ staging" --format='value(name)')
# echo $POLICY 
# projects/two-eye-two-see/alertPolicies/12673409021288629743
gcloud alpha monitoring snoozes create --display-name="Uptime Check Disabled $HUB_NAME" --criteria-policies="$POLICY" --start-time="$(date -Iseconds)" --end-time="+PT7D"
# Created snooze [projects/two-eye-two-see/snoozes/3009021608334458880].
```
