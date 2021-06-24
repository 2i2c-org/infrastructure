# Terraform

[Terraform](https://www.terraform.io/) is used to manage our infrastructure
on Google Cloud Platform. The source files are under `terraform/` in this repo,
and variables defining each cluster we manage are under `terraform/projects`.

## Workspaces

We use [terraform workspaces](https://www.terraform.io/docs/language/state/workspaces.html)
to maintain separate terraform states about different clusters we manage.
There should be one workspace per cluster, with the same name as the `.tfvars`
file with variable definitions for that cluster.

Workspaces are stored centrally in the `two-eye-two-see-org` GCP project, even
when we use Terraform for projects running on AWS / Azure. You must have
access to this project before you can use terraform for our infrastructure.