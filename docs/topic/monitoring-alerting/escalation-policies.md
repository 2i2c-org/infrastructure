# Escalation policies and on-call

Pagerduty creates incidents [only if it can assign them to someone](https://support.pagerduty.com/main/docs/why-incidents-fail-to-trigger#no-one-was-on-call).
This means we need to have an on-call rotation set up that covers all 24h of the day, 7 days a week.

However, because nobody is expected to respond outside working hours, we have a placeholder user associated with the support email address that is used as the user in the on-call rotation when everybody else is outside working hours.

This user gets emailed when an alert is triggered and there is no human being on-call. This allows us to see the alert and respond to it during working hours.

## Escalation policies

The following escalation policies are defined [in PagerDuty](https://2i2c-org.pagerduty.com/escalation_policies?).

1. **Outages or possible outages**
- This escalation policy is connected to the following services in our Service Directory:
   - JupyterHub URL availability
   - Prometheus URL availability
   - Persistent Storage Outage
   - Server Startup Failure
- The alerts triggered under these services, are either 100% a P1 incident or an alert that could signal an undergoing incident.
- It makes use of the **all** users' schedules, including the placeholder user
- It assigns incidents to the on-call user in a Round Robin fashion (choosing from the users that are on-call, in the moment the incident is triggered), escalating to the next user if the incident is not acknowledged within 4h.

2. **Shouldn't be an outage**
- This escalation policy is connected to the following services in our Service Directory:
   - Misc alerts from Prometheus Alert Manager
   - Persistent Storage
   - Pod Restarts
- The alerts triggered under these services are alerts that signal that something is wrong with a hub, and if left unaddressed, it might cause an outage in the future. But they do not usually signal an ongoing outage.
- This policy doesn't include the Technical Lead's schedule
- This policy assigns incidents to the on-call users in a Round Robin fashion, escalating to the next user if the incident is not acknowledged within 12h.

## Paging
**TBD**

Currently, the **desired** paging policy is:
**After an incident is assigned to someone:**
- Immediately, send a Slack DM
- 30 minutes after, send an email
- 1 hour after, send an SMS

```{note}
The placeholder user will only get an email immediately after the incident is assigned to them.
This email will go to the support email address.
```

The `#pagerduty-notifications` channel on Slack will get notified of when an incident is escalated, i.e. it wasn't acknowledged by the person assigned to it by the escalation policy. This way we reduce the number of interruptions the team is exposed to.