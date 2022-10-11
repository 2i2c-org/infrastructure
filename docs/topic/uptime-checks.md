# Simple HTTPS Uptime Checks

Ideally, when a hub is down, a machine alerts us - we do not have to wait for a user
to report it to our helpdesk. While we aren't quite there, we currently have very simple
uptime monitoring for all our hubs. [GCP Uptime Checks](https://cloud.google.com/monitoring/uptime-checks)
are used (because they are free) to hit the `/hub/health` endpoint
of the public URL of all our hubs. If these checks fail for 5 minutes, an alert is sent
to our [PagerDuty](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)
notification channel.

## Where are the checks?

Uptime checks are *centralized* - they don't exist in the same project or cloud provider
as the hubs they are checking, but in one centralized GCP project (`two-eye-two-see`). This
has a few advantages:

1. We do not have to implement the same functionality three times (one per cloud provider),
   as we would have to if this were to exist in the same project as the hub.
2. We use a centralized PagerDuty for alerting, so this Notification Channel can exist in
   only one place. Setting up this channel requires secrets, and we'll have to either add
   secret handling to our terraform code or re-implement setting this up in python 3 times.
3. These are all 'black box' external checks, so it does not particularly matter where they
   come from.

You can browse the existing checks [on the GCP Console](https://console.cloud.google.com/monitoring/uptime?project=two-eye-two-see)
as well.

## How does notification work?

We use PagerDuty for notifying us whenever any of these checks fail. This is
done via a GCP Notification Channel in the `two-eye-two-see` GCP project,
created [following these
instructions](https://cloud.google.com/monitoring/support/notification-options#pagerduty).

```{note}
This Notification Channel was created manually following instructions in the
link provided, not automatically. We *must* automate this if we create another
notification channel, but since a single notification channel is ok for how we
use PagerDuty now, it is fine.
```

When any of the checks fail, they automatically open an Incident in the
[Managed JupyterHubs](https://2i2c-org.pagerduty.com/service-directory/PS10YJ3) service
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
