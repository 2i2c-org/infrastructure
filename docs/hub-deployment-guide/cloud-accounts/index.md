(new-cloud-account)=
# Create new cloud accounts

This documentation provides guides on creating new cloud accounts for our supported cloud providers.

## What is a "cloud account"?

For the purposes of this documentation, a "cloud account" represents a unit of billing.
This concept has different names across the major cloud providers we support, and therefore it's difficult to generalise the term.
For example, "project" on GCP, "account" on AWS, "subscription" on Azure, and so forth.

## When and why do we create new cloud accounts?

We create new cloud accounts when deploying new clusters.
This allows us to exactly determine the spend on a cloud account, ensure the privacy of users on that cloud account from others, as well as making it easier to provide more cloud access to users when necessary.

```{toctree}
:maxdepth: 1
:caption: How to create new cloud accounts for our supported providers
new-gcp-project
new-aws-account
aws-external-account
```
