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

Billing accounts are generally not created often. Usually, you would need to
create a new one for the following reasons:

1. You are getting cloud credits from somewhere, and want a separate container
   for it so you can track spending accurately.
2. You want to use a different credit card than what you use for your other
   billing account.

## AWS

AWS billing is a little more haphazard than GCP's and is derived partially
from the well-established monstrosity that is [LDAP](https://en.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol).

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
*not* an AWS Organization. This is a historical artefact - AWS Organizations
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
relationship with Microsoft and their billing gets managed as part of
that.
