# Calculate how much cloud infrastructure costs

We have several community contracts where we first pay their cloud bills and
then invoice them for it. Any community paying their cloud bills through 2i2c
_must_ have their hub(s) under a `cluster.yaml` file declaring
`[gcp|aws].billing.paid_by_us=true`.

Practically to invoice these communities, we update a [spreadsheet for billing]
summarizing monthly costs for communities, and then request invoicing help from
CS&S via the `#billing` slack channel.

This documentation helps you update that spreadsheet!

```{important}
Make sure you have access to the [spreadsheet for billing] before
following the steps below. Your 2i2c.org email should give you access.
```

[spreadsheet for billing]: https://docs.google.com/spreadsheets/d/1AWVCg0D_-ATub_cVsIy5XZCwqnC6uIcgwDGYK9Q7yno/edit#gid=1349808947

## AWS

### Get costs manually via the UI (only documented option)

```{note}
As of 2024-04-17, we only manage the cost for AWS accounts associated with our
AWS management account. If a future cluster deviates from this, you can tell by
`aws.billing.paid_by_us` being set true in its `cluster.yaml`.
```

1. Login to shared AWS SSO at https://2i2c.awsapps.com/start#/
2. Select the `2i2c-sandbox` account, as it is the primary billing account
3. Select 'AdministratorAccess' to open the AWS Console for this account
4. Visit the "Monthly Costs By Linked Account" report ([direct link]) via "Billing and Cost Management" -> "Cost Explorer Saved Reports"
5. On the right sidebar under "Time -> Date Range", select all the completed months we want to get data for
6. On the right sidebar under "Time -> Granularity", ensure its selected as "Monthly"
7. Click the 'Download as CSV' button
8. Copy AWS costs

   The CSV file has rows for each month, and columns for each project. Copy it
   into the spreadsheet, making sure the rows and columns both match what is
   already present. The AWS account name should match the "Cloud Project" row in
   the spreadsheet.

   Once done, re-check the numbers once again to make sure they were copied
   correctly.

[direct link]: https://us-east-1.console.aws.amazon.com/costmanagement/home?region=us-east-1#/cost-explorer?reportId=d826a775-e0d6-4e85-a181-7f87a8deb162&reportName=Monthly%20costs%20by%20linked%20account&isDefault=true&chartStyle=GROUP&historicalRelativeRange=LAST_6_MONTHS&futureRelativeRange=CUSTOM&granularity=Monthly&groupBy=%5B%22LinkedAccount%22%5D&filter=%5B%5D&costAggregate=unBlendedCost&showOnlyUntagged=false&showOnlyUncategorized=false&useNormalizedUnits=false

## GCP

### Get costs manually via the UI (recommended)

```{important}
Currently this is the recommended way of retrieving the costs from GCP.
```

1. Go to the [2i2c billing account] on GCP
2. Select 'Reports' on the left sidebar
3. Under time range on the right sidebar, select 'Invoice Month'
4. Select the time range you are interested in. Note that this has to be at least two months right now, or the next step does not work
5. Under 'Group by', select 'Month -> Project'.
6. Under the chart, click the 'Download CSV' button. This downloads a CSV that you can use to later populate the columns in the costs spreadsheet
   ```{figure} ../images/gcp-billing-ui.png
   GCP billing UI
   ```
7. Copy GCP costs.

   The GCP CSV has rows for each month and project. Carefully copy the $ values under
   'subtotal' (last column) into the [spreadsheet for billing]. Match the 'project name' column in the GCP CSV with the 'cloud project' row in our billing spreadsheet.

   When done, re-check the numbers once again to make sure they are copied correctly.

[2i2c billing account]: https://console.cloud.google.com/billing/0157F7-E3EA8C-25AC3C/reports;timeRange=CUSTOM_RANGE;from=2024-01-01;to=2024-01-31;dateType=INVOICE_DATE;invoiceCorrections=TAX,BILLING_MODIFICATION?organizationId=184174754493&project=two-eye-two-see

### Get costs automatically via the deployer (not ready to be used yet!)

```{warning}
This deployer command requires more development work and is not yet recommended to be used.
```

The `generate cost-table` subcommand of the `deployer` will go through all our
clusters set up on Google Cloud, and tell you how much they cost.

Pre-requisites for running it:

1. You have all [tools required](tutorials:setup) required to work on this repo
   setup.

2. Run `gcloud application-default auth login`, and authenticate with your `2i2c.org`
   google account. This account *must* have permissions to all GCP projects. This
   requirement will be relaxed at some point in the future.

There is a private [Google Sheet](https://docs.google.com/spreadsheets/d/1URYCMap-Lxm4e_pAAC3Esxda7tZzRhCS6d85pxUiVQs/edit#gid=0)
that has monthly costs for all the clusters that are configured to have
[bigquery export](new-gcp-project:billing-export).

This sheet is currently manually updated. You can update it by running
`deployer generate cost-table --output 'google-sheet'`. It will by default
update the sheet to provide information for the last 12 months. You can control
the period by passing in the `start_month` and `end_month` parameters.

If you just want to take a look at the costs in the terminal, you can also run
`deployer generate cost-table --output 'terminal'` instead.

```{warning}
If the script is run before the end of the month, the total costs would not
be accurate. Run the script once the month has finished to get an accurate
amount of the previous month's costs.
```

#### Caveats

1. The data comes from [bigquery costs export](new-gcp-project:billing-export), so
   is only available and accurate after that has been enabled. For billing data
   before this was enabled, you need to manually go look in the cloud console.

#### Other Cloud Cost Reporting Exporting

- [AWS Cost and Usage Report](https://docs.aws.amazon.com/cur/latest/userguide/cur-create.html)
- [Azure Cost Export](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-export-acm-data?tabs=azure-portal)
