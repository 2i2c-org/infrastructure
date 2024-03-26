# Calculate how much cloud infrastructure costs

We have several contracts where we pay for our users' cloud bills,
and then invoice them for it. We need to automate the process of figuring
out how much these organizations owe us.

```{important}
Make sure you have access to [this sheet](https://docs.google.com/spreadsheets/d/1AWVCg0D_-ATub_cVsIy5XZCwqnC6uIcgwDGYK9Q7yno/edit#gid=1349808947) before following the steps below. Your 2i2c.org email should give you access.
```

## GCP

### Get costs manually via the UI (recommended)

```{important}
Currently this is the recommended way of retrieving the costs from GCP.
```

1. Go to the [2i2c billing account](https://console.cloud.google.com/billing/0157F7-E3EA8C-25AC3C/reports;timeRange=CUSTOM_RANGE;from=2024-01-01;to=2024-01-31;dateType=INVOICE_DATE;invoiceCorrections=TAX,BILLING_MODIFICATION?organizationId=184174754493&project=two-eye-two-see) on GCP
2. Select 'Reports' on the left sidebar
3. Under time range on the right sidebar, select 'Invoice Month'
4. Select the time range you are interested in. Note that this has to be at least two months right now, or the next step does not work
5. Under 'Group by', select 'Month -> Project'.
6. Under the chart, click the 'Download CSV' button. This downloads a CSV that you can use to later populate the columns in the costs spreadsheet
   ```{figure} ../../images/gcp-billing-ui.png
   GCP billing UI
   ```
7. Copy GCP costs
   The GCP CSV has rows for each month and project. Carefully copy the $ values under
   'subtotal' (last column) into [our billing spreadsheet]((https://docs.google.com/spreadsheets/d/1AWVCg0D_-ATub_cVsIy5XZCwqnC6uIcgwDGYK9Q7yno/edit#gid=1349808947)). Match the 'project name' column in the GCP CSV with the 'cloud project' row in our billing spreadsheet.

   When done, re-check the numbers once again to make sure they are copied correctly.

### Get costs automatically via the deployer (under development)

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

Caveat:
- If the script is run before the end of the month, the total costs would not
  be accurate. Run the script once the month has finished to get an accurate
  amount of the previous month's costs.

## Caveats

1. The data comes from [bigquery costs export](new-gcp-project:billing-export), so
   is only available and accurate after that has been enabled. For billing data
   before this was enabled, you need to manually go look in the cloud console.

   ## Other Cloud Cost Reporting Exporting

   - [AWS Cost and Usage Report](https://docs.aws.amazon.com/cur/latest/userguide/cur-create.html)
   - [Azure Cost Export](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-export-acm-data?tabs=azure-portal)