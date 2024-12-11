(hub-deployment-guide:runbooks:phase1)=
# Phase 1: Account setup

This phase is applicable for cases where a new cluster needs to be setup to accommodate the new hub. This allows us to exactly determine the spend on a cloud account, ensure the privacy of users on that cloud account from others, as well as making it easier to provide more cloud access to users when necessary.

```{note}
For the purposes of this documentation, an "account" represents a unit of billing. This concept has different names across the major cloud providers we support, and therefore it's difficult to generalise the term.
For example, "project" on GCP, "account" on AWS, "subscription" on Azure, and so forth.
```

## Definition of ready

The following lists the information that needs to be available to the engineer before this phase can start.

- Cloud Provider
- Will 2i2c pay for cloud costs and recover them via invoice?
- Target Start Date
- Community Representatives
- Technical Contacts added to Airtable?

## Default cloud provider

*If* the community has no particular preference for a cloud
provider, we will default to using AWS.

## Outputs

At the end of Phase 1, all engineers should have access to the cloud account where the new cluster and hub will be deployed to.

No file assets will be generated at the end of this phase.

## Available runbooks

Based on the information provided, choose one of the following runbooks to follow.

```{toctree}
:maxdepth: 1
new-gcp-project
new-aws-account
aws-external-account
```
