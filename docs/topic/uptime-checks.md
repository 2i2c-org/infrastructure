# Simple HTTPS Uptime Checks

Ideally, when a hub is down, a machine alerts us - we do not have to wait for a user
to report it to our helpdesk. While we aren't quite there, we currently have very simple
uptime monitoring for all our hubs. [GCP Uptime Checks](https://cloud.google.com/monitoring/uptime-checks)
are used (because they are free) to hit the `/hub/health` endpoint
of the public URL of all our hubs. If these checks fail for 5 minutes, an alert is sent
to our [PagerDuty](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/incidents.html)
notification channel. This automatically posts a message in the `#pagerduty-notifications`
channel in the 2i2c slack, and starts an incident in PagerDuty - kicking off the incident
response process.

## Notification Channel

When any of the checks fail, they automatically open an Incident in the
[Managed JupyterHubs](https://2i2c-org.pagerduty.com/service-directory/PS10YJ3) service
we maintain in PagerDuty. This is done via a GCP Notification Channel in the `two-eye-two-see`
GCP project, created [following these instructions](https://cloud.google.com/monitoring/support/notification-options#pagerduty).

## Changing the configuration of the checks

If you change the configuration of the checks themselves (such as their frequency,
target URL, etc) - `ensure-uptime-checks` will *not* modify currently existing checks. The new
config will only be applied to new checks. You will need to run
`python3 deployer ensure-uptime-checks --force-recreate` - this will delete all existing
UptimeChecks and AlertPolicies and recreate them, making sure your changes are applied to
everything.
