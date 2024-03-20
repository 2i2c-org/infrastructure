# Billing reports

## Billing reports in the web console

Cloud providers provide a billing console accessible via the web, often
with very helpful reports. While not automation-friendly (see next section
for more information on automation), this is very helpful for doing ad-hoc
reporting as well as trying to optimize cloud costs. For dedicated clusters,
this may also be directly accessible to hub champions, allowing them to
explore their own usage.

### GCP

You can get a list of all billing accounts you have access to via the [billing console](https://console.cloud.google.com/billing)
(make sure you are logged in to the correct Google account). Alternatively,
you can select 'Billing' from the left sidebar in the Google Cloud Console
after selecting the correct project.

Once you have selected a billing account, you can access a reporting
interface by selecting 'Reports' on the left sidebar. This lets you group
costs in different ways, and explore that over different time periods.
Grouping and filtering by project and service (representing
what kind of cloud product is costing us what) are the *most useful* aspects
here. You can also download whatever you see as a CSV, although programmatic
access to most of the reports here is unfortunately limited.

### AWS

For AWS, "Billing and Cost Management" is accessed from specific AWS
accounts. If using consolidated billing, it must be accessed from the
'management account' for that particular organization (see previous section
for more information).

You can access "Billing and Cost Management" by typing "Billing and Cost
Management" into the top search bar once you're logged into the correct
AWS account. AWS has a million ways for you to slice and dice these reports,
but the most helpful place to start is the "Cost Explorer Saved Reports".
This provides 'Monthly costs by linked account' and 'Monthly costs by
service'. Once you open those reports, you can further filter and group
as you wish. A CSV of reports can also be downloaded from this page.

### Azure

We have limited expertise here, as we have never actually had billing
access to any Azure account!

## Programmatic access to billing information

The APIs for getting access to billing data *somehow* seem to be the
least well-developed parts of any cloud vendor's offerings. Usually,
they take the form of a 'billing export' - you set up a *destination*
where information about billing is written, often once a day. Then
you query this location for billing information. This is in sharp contrast
to most other cloud APIs, where the cloud vendor has a *single source of
truth* you can just query. Not so for billing - there's no external API
access to the various tools they seem to be able to use to provide the
web UIs. This also means we can't get *retroactive* access to billing data -
if we don't explicitly set up export, we have **no** programmatic access
to billing information. And once we set up export, we will only have
access from that point onwards, not retrospectively.

1. GCP asks you to set up [export to BigQuery](https://cloud.google.com/billing/docs/how-to/export-data-bigquery),
   their sql-like big data product. In particular, we should prefer setting
   up [detailed billing export](https://cloud.google.com/billing/docs/how-to/export-data-bigquery-tables/detailed-usage).
   This is set up **once per billing account**, and **not once per project**.
   And one billing account can export only to BigQuery in one project, and
   you can not easily move this table from one project to another. New
   data is written into this once a day, at 5 AM Pacific Time.

2. AWS asks you to set up [export to an S3 bucket](https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html),
   where CSV files are produced once a day. While we *could* then import
   this [into AWS Athena](https://docs.aws.amazon.com/cur/latest/userguide/cur-query-athena.html)
   and query it, directly dealing with S3 is likely to be simpler for
   our use cases. This data is also updated daily, once enabled.

3. Azure is unknown territory for us here, as we have only supported Azure
   for communities that bring their own credits and do their own cost
   management.

Our automated systems for billing need to read from these 'exported'
data sources, and we need to develop processes to make sure that
we *do* have the billing data exports enabled correctly.