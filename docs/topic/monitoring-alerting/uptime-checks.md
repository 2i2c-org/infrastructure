(uptime-checks)=
# Simple HTTPS uptime checks

Ideally, when a hub is down, a machine alerts us - we do not have to wait for a user
to report it to our helpdesk. While we aren't quite there, we currently have very simple
uptime monitoring for all our hubs with free [GCP Uptime Checks](https://cloud.google.com/monitoring/uptime-checks).

## Where are the checks?

Uptime checks are *centralized* - they don't exist in the same project or cloud provider
as the hubs they are checking, but in one centralized GCP project (`two-eye-two-see`). This
has a few advantages:

1. We do not have to implement the same functionality three times (one per cloud provider),
   as we would have to if this were to exist in the same project as the hub.
2. These are all 'black box' external checks, so it does not particularly matter where they
   come from.

You can browse the existing checks [on the GCP Console](https://console.cloud.google.com/monitoring/uptime?project=two-eye-two-see)
as well.

## Cost

Note that as of October 2022 [Google Stackdriver
Pricing](https://cloud.google.com/stackdriver/pricing) the free monthly quota is
1 million executions of uptime checks per project.

| Feature | Price | Free allotment per month | Effective date |
| --- | --- | --- | --- |
| Execution of Monitoring uptime checks| $0.30/1,000 executions| 1 million executions per Google Cloud project|	October 1, 2022 |

## When are notifications triggered?

Our uptime checks are performed every 15 minutes, and we alert if checks have failed for 31 minutes.
This make sure there are at least 2 failed checks before we alert.

We are optimizing for *actionable alerts* that we can completely *trust*,
and prevent any kind of alert fatigue for our engineers.

### JupyterHub health checks

The JupyterHub *does* get restarted during deployment, and this can cause a few
seconds of downtime - and we do not want to alert in case the uptime check hits
the hub *just* at that moment. We trade-off a few minutes of responsiveness for
trust here. `/hub/health` is the endpoint checked for hubs, and `/health` is checked
for binderhub.

When an alert is triggered, it automatically opens an Incident in the
[Managed JupyterHubs](https://2i2c-org.pagerduty.com/service-directory/PS10YJ3) service
we maintain in PagerDuty. This also notifies the `#pagerduty-notifications` channel on
the 2i2c slack, and kicks off [our incident response process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)

### Prometheus health checks

Our prometheus instances are protected by auth, so we just check to see if we get a
`401 Unauthorized` response from the prometheus instance.

When an alert is triggered, it automatically opens an Incident in the
[Cluster Prometheus](https://2i2c-org.pagerduty.com/service-directory/P4B7MEA) service
we maintain in PagerDuty. This also notifies the `#pagerduty-notifications` channel on
the 2i2c slack, and kicks off [our incident response process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)


## How are the checks set up?

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
## How do I snoooze a check?

As the checks are all in GCP they can be created through the [monitoring console](https://console.cloud.google.com/monitoring/alerting?project=two-eye-two-see).

The `alpha` gcloud component also supports setting snoozes from the command line. For further documentation see the [Google Cloud Monitoring docs](https://cloud.google.com/monitoring/alerts/manage-snooze#gcloud-cli) or the [gcloud alpha monitoring snoozes](https://cloud.google.com/sdk/gcloud/reference/alpha/monitoring/snoozes) reference. You may need to add the `alpha` component to your `gcloud` install.


Example CLI use that snoozes binder-staging check for 7 days:

```
HUB=binder-staging
POLICY=$(gcloud alpha monitoring policies list  --filter "displayName ~ binder-staging" --format='value(name)')
# echo $POLICY 
# projects/two-eye-two-see/alertPolicies/12673409021288629743
gcloud alpha monitoring snoozes create --display-name="Uptime Check Disabled $HUB" --criteria-policies="$POLICY" --start-time="$(date -Iseconds)" --end-time="+PT7D"
# Created snooze [projects/two-eye-two-see/snoozes/3009021608334458880].
```
