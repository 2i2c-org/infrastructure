# Billing accounts

Cloud providers have different ways of attaching a source of money
(a credit card or cloud credits) to the resources we get charged for.

## GCP

A [Billing Account](https://cloud.google.com/billing/docs/how-to/manage-billing-account)
is the unit of billing in GCP. It controls:

1. The **source** of funds - credit cards, cloud credits, other invoicing mechanisms
2. Detailed reports about how much money is being spent
3. Access control to determine who has access to view the reports, attach new projects to the billing account, etc
4. Configuration for where data about what we are being billed for should be
   exported to. See the "Programmatic access to billing information" section
   for more details.

Multiple [Projects](https://cloud.google.com/storage/docs/projects) can
be attached to a single billing account, and projects can usually move
between billing accounts. All cloud resources (clusters, nodes, object storage,
etc) are always contained inside a Project.

Billing accounts are generally not created often. Usually you would need to
create a new one for the following reasons:

1. You are getting cloud credits from somewhere, and want a separate container
   for it so you can track spend accurately.
2. You want to use a different credit card than what you use for your other
   billing account.

## AWS

AWS billing is a little more haphazard than GCP's, and derived partially
from the well established monstrosity that is [LDAP](https://en.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol).

We will not dig too deep into it, lest we wake some demons. However, since
we are primarily concerned with billing, understanding the following concepts
is more than enough.

1. An [AWS Account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html#account)
   contains all the cloud resources one may create.
2. An [AWS Organization](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html)
   is a way to *group* multiple AWS accounts together. One AWS Account in
   any AWS Organization is deemed the [management account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html#account).
   The management account sets up access control, billing access, billing
   data export, etc for the entire organization.

Each AWS Account can have billing attached in one of two ways:

1. Directly attached to the account, via a credit card or credits
2. If the account is part of an AWS Organization, it can use the billing
   information of the *Management Account* of the organization it is a
   part of. This is known as [consolidated billing](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/consolidated-billing.html)

So billing information is *always* associated with an AWS Account,
*not* AWS Organization. This is a historical artifact - AWS Organizations
were only announced [in 2016](https://aws.amazon.com/about-aws/whats-new/2016/11/announcing-aws-organizations-now-in-preview/),
a good 9 years after AWS started. So if this feels a little hacked on,
it is because it is!

A pattern many organizations (including 2i2c) follow is to have an AWS Account
that is completely empty and unused, except for being designated as the
management account. Billing information (and credits) for the entire
organization is attached to this account. This makes access control much
simpler, as the only people who get access to this AWS account are those
who need to handle billing.

## Azure

We currently have no experience or knowledge here, as all our Azure
customers handle billing themselves. This is not uncommon - most Azure
users want to use it because they already have a pre-existing *strong*
relationship with Microsoft, and their billing gets managed as part of
that.

## Billing reports in the web console

Cloud providers provide a billing console accessible via the web, often
with very helpful reports. While not automation friendly (see next section
for more information on automation), this is very helpful for doing ad-hoc
reporting as well as trying to optimize cloud costs. For dedicated clusters,
this may also be directly accessible to hub champions, allowing them to
explore their own usage.

### GCP

You can get a list of all billing accounts you have access to [here](https://console.cloud.google.com/billing)
(make sure you are logged in to the correct google account). Alternatively,
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
as you wish. A CSV of reports can also be downloaded here.

### Azure

We have limited expertise here, as we have never actually had billing
access to any Azure account!

## Programmatic access to billing information

The APIs for getting access to billing data *somehow* seem to be the
least well developed parts of any cloud vendor's offerings. Usually
they take the form of a 'billing export' - you set up a *destination*
where information about billing is written, often once a day. And then
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
   And one billing account can export only to bigquery in one project, and
   you can not easily move this table from one project to another. New
   data is written into this once a day, at 5AM Pacific Time.

2. AWS asks you to set up [export to an S3 bucket](https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html),
   where CSV files are produced once a day. While we *could* then import
   this [into AWS Athena](https://docs.aws.amazon.com/cur/latest/userguide/cur-query-athena.html)
   and query it, directly dealing with S3 is likely to be simpler for
   our use cases. This data is also updated daily, once enabled.

3. Azure is unknown territory for us here, as we have only supported Azure
   for communities that bring their own credits and do their own cost
   management.

Our automated systems for billing need to read from these 'exported'
data sources, and we need to develop processes for making sure that
we *do* have the billing data exports enabled correctly.