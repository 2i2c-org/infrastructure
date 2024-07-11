(howto:enable-budget-alerts)=
# Enable Budget Alerts

This document describes how to enable budget alerts for a cluster.

```{note}
This feature is currently only available on GCP!
```

## GCP

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
