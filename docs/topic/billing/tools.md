# Cloud billing tools

There are a few tools we can use to make cloud billing easier to understand,
reason about and use.

## Using tags to separate costs

Cloud billing reports by default allow us to see how much each **service**
was charged for - for example, we could know that VMs cost us $589.
But wouldn't it be nice to know how much of that $589 was for core nodes,
how much was for user nodes, and how much for dask workers? Or
hypothetically, if we had multiple profiles that were accessible only to
certain subsets of users, which profiles would cost how much money?

This is actually possible if we use **tags to track cost**, which can be attached
to *most* cloud resources (**not** Kubernetes resources). Once attached
to specific sets of resources, you can filter and group by them in the
web reporting UI or programmatically in the billing export. This will
count *all* costs emanating from any resource tagged with that tag. For
example, if a node is tagged with a particular tag, the following separate
things will be associated with the tag:

1. The node's memory
2. The node's CPU
3. (If tagged correctly) The node's boot disk
4. Any network costs accrued by actions of processes on that node (subject
   to some complexity)

However, they have quite a few limitations as well:

1. They are attached to *cloud* resources, *not* Kubernetes resources. By
   default, multiple users can be on a single node, so deeper granularity
   of cost attribution is not possible.
2. Some cloud resources are shared to reduce cost (home directories are a
   prime example), and detailed cost attribution there needs to be done
   via other means.
3. This does not apply retroactively, you must already have the tags set up
   for costs to be accrued to them.

Despite these limitations, cost tagging is extremely important to get a good
understanding of what and how much costs money. With a well-tagged system, we
can make reasoned trade-offs about cost rather than fiddling in the dark.

Resource links: [GCP Labels](https://cloud.google.com/compute/docs/labeling-resources), [AWS Cost Allocation Tags](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html), [Azure Tags](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/enable-tag-inheritance)

## Budget alerts

All cloud providers allow us to set up alerts that fire whenever a particular
project is about to cost more than a specific amount, or is forecast to go over a specific amount by the end of the month if current trends continue.
This can be *extremely helpful* in assuaging communities of cost overruns
but requires we have a prediction for *what numbers* to set these budgets at,
as well as what to do when the alerts fire. Usually, these alerts can be
set up manually in the UI or (preferably) via Terraform. We currently only
utilise these on GCP, and more details can be found in [](topic:billing:budget-alerts).

More information: [GCP](https://cloud.google.com/billing/docs/how-to/budgets), [AWS](https://aws.amazon.com/aws-cost-management/aws-budgets/)
and [Azure](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-mgt-alerts-monitor-usage-spending).