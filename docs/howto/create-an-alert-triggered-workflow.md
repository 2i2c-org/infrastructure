(alert-triggered-workflow)=
# Create an GitHub workflow that's triggered by a Pagerduty alert

Sometimes, it's useful to be able to run a GitHub workflow for and alert that has been triggered in Pagerduty.
To do so, we can use Pagerduty's [incident workflow](https://support.pagerduty.com/main/docs/incident-workflows) feature.

## Steps

### On the PagerDuty side

1. Go to [the list of incident workflows](https://2i2c-org.pagerduty.com/incident-workflows/workflows?sortDirection=asc) and click the `New Workflow` button in the right side of the screen.

2. Give it a suggestive name and click the `Create` button

3. In the `Builder` section, click `Add Trigger` and choose the desired one

4. When you're happy with the trigger, click the `Add Action` button

5. From the list of actions, search after `Send a Webhook POST`, select it once you find it and click the `Add Action button` on the right

6. After adding the `Send a Webhook POST` action, a menu should have been opened for you on the right side of the screen

7. In that menu, enter the following:
   - **URL**: https://api.github.com/repos/2i2c-org/infrastructure/dispatches
   - **Authentication Headers**: Geo-GitHub conn
   - **Headers**:
     ```yaml
     Content-Type: application/json
     Accept:application/vnd.github.v3+json
     ```
   - **Body**
     ```json
     {
       "event_type": "some-relevant-keyword-for-matching-this-event",
       "client_payload": {
         "incident_id": "{{incident.id}}",
         "title": "{{incident.title}}",
         "service": "{{incident.service.name}}",
         "type": "{{incident.incident_type.display_name}}"
       }
     }
     ```
   ```{note}
   Note that the event type is what's going to be used by GitHub to trigger or not the workflow.
   Also, other things can be included in the payload. Experiment!
   ```

### On the GitHub side

1. Create a new workflow file in `.github/workflows`

2. In this file, the following info is important:

   ```yaml
    name: P1 outages actions
    on:
      repository_dispatch:
        types: [some-relevant-keyword-for-matching-this-event]
    ```

3. Add the jobs you want

Now, this workflow will run every time the conditions set in the incident workflow you set up, if they match the following `some-relevant-keyword-for-matching-this-event` type.