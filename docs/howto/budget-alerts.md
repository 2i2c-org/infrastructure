(howto:setting-up-budget-alerts)=
# Setting up Budget Alerts

As of July 2024, we look to setup budget alerts for all cloud projects where we
pay the bill from the cloud provider, independently if we pass through these
costs or not to the community. We currently don't look to setup budget alerts
for communities paying their cloud provider bill directly.

This document describes how to enable (or opt-out of) budget alerts for a
cluster via the cluster's associated terraform variables file (`.tfvars`).

`````{tab-set}
````{tab-item} AWS
:sync: aws-key

AWS budget alerts are setup by default. To opt-out, declare:

```
default_budget_alert = {
  "enabled" : false,
}
```
````

````{tab-item} GCP
:sync: gcp-key

```{attention}
We can only enable budget alerting on GCP projects where we have enough permissions to enable APIs and view the billing account.
```

First, ensure the following APIs are enable on the GCP project you'd like to enable budget alerting for:

- [Cloud Resource Manager API](https://console.cloud.google.com/apis/library/cloudresourcemanager.googleapis.com)
- [Cloud Billing Budget API](https://console.cloud.google.com/apis/library/billingbudgets.googleapis.com)

Then edit the following variables in the relevant `.tfvars` file for the cluster.

- **Set `budget_alert_enabled = false`**, or delete the variable altogether (it is set to `true` in the `variables.tf` file).
  This will ensure that the relevant resources will be created by terraform.
- **Set `billing_account_id`.**
  This is the ID for the billing account linked to the project.
  - You can find the ID by visiting the [Billing console](https://console.cloud.google.com/billing/linkedaccount?project=two-eye-two-see), ensuring the correct project is selected in the dropdown at the top.
    In the dialogue box, click "Go to Linked Billing Account", and then click "Manage Billing Account" along the top.
    This will open a pane that gives you the Billing Account ID.
  - For accounts that we don't manage, the process is the same but _we may not have permission to view the Billing Account ID_.
    In this case, we cannot enable budget alerting for this project.

With these variables set, you are ready to open a PR and perform a terraform apply!
````

````{tab-item} Azure
:sync: azure-key

To enable budget alerts for an Azure cluster, edit the following variables in the relevant `.tfvars` file for the cluster.

- **Set `budget_alert_enabled = true`**

  This will ensure that the relevant resources will be created by terraform.

- **Set `budget_alert_amount`**

  Current practice is to set this to the average expenditure of the last 3 months.

  Then the alert will be triggered when the forecasted cost will exceed this value plus 20%.

  You can find values to calculate that in the Cost analysis tab of the relevant Azure subscription: `Azure subscription` -> `Cost Management` -> `Cost analysis`.

  If you are setting this up for a new cluster, you obviously don't have this information yet!
  Instead, set the value to something like `500` and we can adjust as the community begins to use it.

- With these variables set, you are ready to open a PR and perform a terraform apply!
````
`````
