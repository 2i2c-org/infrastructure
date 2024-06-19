# Calculate how much cloud infrastructure costs

We have several community contracts where we first pay their cloud bills and
then invoice them for it. Any community paying their cloud bills through 2i2c
_must_ have their hub(s) under a `cluster.yaml` file declaring
`[gcp|aws].billing.paid_by_us=true`.

Practically to invoice these communities, we update a [spreadsheet for billing]
summarizing monthly costs for communities, and then request invoicing help from
CS&S via the `#billing` slack channel.

```{important}
If you do not have access to the `#billing` slack channel, ask in the
`#team-updates` channel and someone will add you.
```

This documentation helps you update that spreadsheet for communities on shared
clusters and generate CSV files for dedicated clusters.

```{important}
Make sure you have access to the [cloud costs folder] and [spreadsheet for billing]
before following the steps below. Your 2i2c.org email should give you access.
```

[cloud costs folder]: https://drive.google.com/drive/folders/1_xXZ2ndEOplZidG_mj6nmUTzsOuxARcL?usp=drive_link
[spreadsheet for billing]: https://docs.google.com/spreadsheets/d/1AWVCg0D_-ATub_cVsIy5XZCwqnC6uIcgwDGYK9Q7yno/edit#gid=1349808947

## Communities in shared cloud accounts

The procedure for GCP projects and AWS accounts is similar. It is practically
demonstrated in a ~20 minute [video] working in a [spreadsheet for accounting of
cost for communities in shared clusters].

The procedure from the video is:

1. Open the [spreadsheet for accounting of cost for communities in shared
   clusters].
2. Duplicate the page for the previous month and clear outdated values in green
   cells.
3. Use guidance in pink cells to fill in green cells and finally verify a sum.
4. Protect the page by right clicking on its tab in order to warn users trying
   to edit it going onwards.
5. Enter the verified monthly community costs in the [spreadsheet for billing]
   and double check anything looking odd in relation to previous months' values.

[video]: https://drive.google.com/file/d/1NQAVo3iJuuaDAp5WI0uinY148M9IK1Ty/view?usp=drive_link
[spreadsheet for accounting of cost for communities in shared clusters]: https://docs.google.com/spreadsheets/d/1tzKlNBkJiqmm_eTO7dqxIYugverZNi_zSlmBWP3Ek5E/edit#gid=120717885

## Communities with dedicated cloud accounts

### Get a community dedicated AWS accounts's costs

```{note}
As of 2024-04-17, we only manage the cost for AWS accounts associated with our
AWS management account. If a future cluster deviates from this, you can tell by
`aws.billing.paid_by_us` being set true in its `cluster.yaml`.
```

1. Login to shared AWS SSO at <https://2i2c.awsapps.com/start#/>
1. Select the `2i2c-sandbox` account, as it is the primary billing account
1. Select 'AdministratorAccess' to open the AWS Console for this account
1. Visit the "Monthly Costs By Linked Account" report ([direct link]) via "Billing and Cost Management" -> "Cost Explorer Saved Reports"
1. On the right sidebar under "Time -> Date Range", select all the completed months we want to get data for
1. On the right sidebar under "Time -> Granularity", ensure its selected as "Monthly"
1. On the right sidebar under "Group by -> Dimension", select "Linked account"
1. Click the 'Download as CSV' button
   ```{figure} ../images/aws-billing-ui.jpg
   AWS billing UI
   ```
1. Run the following deployer command to convert the generated CSV file into the format required for the invoicing process.
   
   ```bash
   deployer transform cost-table aws pathto/downloaded/csvfile
   ```

   This will output a new CSV file to your local filesystem called `AWS_{START_MONTH}_{END_MONTH}.csv`.
2. Upload this CSV file to the [cloud costs folder]
3. Ping the folks in the `#billing` slack channel to let them know the info for dedicated clusters is now available and provide a link to the file you have just uploaded

[direct link]: https://us-east-1.console.aws.amazon.com/costmanagement/home?region=us-east-1#/cost-explorer?reportId=d826a775-e0d6-4e85-a181-7f87a8deb162&reportName=Monthly%20costs%20by%20linked%20account&isDefault=true&chartStyle=GROUP&historicalRelativeRange=LAST_6_MONTHS&futureRelativeRange=CUSTOM&granularity=Monthly&groupBy=%5B%22LinkedAccount%22%5D&filter=%5B%5D&costAggregate=unBlendedCost&showOnlyUntagged=false&showOnlyUncategorized=false&useNormalizedUnits=false

### Get a community dedicated GCP projects' costs

```{important}
Currently this is the recommended way of retrieving the costs from GCP.
```

1. Go to the [2i2c billing account] on GCP
1. Select 'Reports' on the left sidebar
1. Under time range on the right sidebar, select 'Invoice Month'
1. Select the time range you are interested in. Note that this has to be at least two months right now, or the next step does not work
1. Under 'Group by', select 'Month -> Project'.
1. Under the chart, click the 'Download CSV' button. This downloads a CSV that you can use to later populate the columns in the costs spreadsheet
   ```{figure} ../images/gcp-billing-ui.png
   GCP billing UI
   ```
1. Run the following deployer command to convert the generated CSV file into the format required for the invoicing process.
   
   ```bash
   deployer transform cost-table gcp pathto/downloaded/csvfile
   ```

   This will output a new CSV file to your local filesystem called `GCP_{START_MONTH}_{END_MONTH}.csv`.
2. Upload this CSV file to the [cloud costs folder]
3. Ping the folks in the `#billing` slack channel to let them know the info for dedicated clusters is now available and provide a link to the file just uploaded

[2i2c billing account]: https://console.cloud.google.com/billing/0157F7-E3EA8C-25AC3C/reports;timeRange=CUSTOM_RANGE;from=2024-01-01;to=2024-01-31;dateType=INVOICE_DATE;invoiceCorrections=TAX,BILLING_MODIFICATION?organizationId=184174754493&project=two-eye-two-see

## Experimental

We have an unfinished attempt to automate collection of community monthly costs.
This heading retains documentation about that, but we are for 2024 not driving
development here and instead relying on the manual approaches.

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
