# Calculate how much cloud infrastructure costs

We have several contracts where we pay for our users' cloud bills,
and then invoice them for it. We need to automate the process of figuring
out how much these organizations owe us.

## Costs for hubs with dedicated clusters on GCP

The `generate-cost-table` subcommand of the `deployer` will go through all our
clusters set up on Google Cloud, and tell you how much they cost.

### Pre-requisites for running it

1. You have all [tools required](tutorials:setup) required to work on this repo
   setup.

2. Run `gcloud application-default auth login`, and authenticate with your `2i2c.org`
   google account. This account *must* have permissions to all GCP projects. This
   requirement will be relaxed at some point in the future.

## Updating the Costs Google Sheet

There is a private [Google Sheet](https://docs.google.com/spreadsheets/d/1URYCMap-Lxm4e_pAAC3Esxda7tZzRhCS6d85pxUiVQs/edit#gid=0)
that has monthly costs for all the clusters that are configured to have
[bigquery export](new-gcp-project:billing-export).

This sheet is currently manually updated. You can update it by running
`deployer generate-cost-table --output 'google-sheet'`. It will by default
update the sheet to provide information for the last 12 months. You can control
the period by passing in the `start_month` and `end_month` parameters.

If you just want to take a look at the costs in the terminal, you can also run
`deployer generate-cost-table --output 'terminal'` instead.

## Caveats

1. The data comes from [bigquery costs export](new-gcp-project:billing-export), so
   is only available and accurate after that has been enabled. For billing data
   before this was enabled, you need to manually go look in the cloud console.

2. If the script is run before the end of the month, the total costs would not
   be accurate. Run the script once the month has finished to get an accurate
   amount of the previous month's costs.


   ## Other Cloud Cost Reporting Exporting

   - [AWS Cost and Usage Report](https://docs.aws.amazon.com/cur/latest/userguide/cur-create.html)
   - [Azure Cost Export](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-export-acm-data?tabs=azure-portal)