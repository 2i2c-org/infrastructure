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

You can initialise using the following command

```bash
terraform init -backend-config=backends/default-backend.hcl
```

## Other remote state storage

For some projects where we don't have access to using our 2i2c accounts, e.g. universities that require us to have specific university-affiliated identities, we can configure different backends to access the terraform state stored in those projects.
Working this way saves us the pain of trying to work with terraform using two different authentications.
The backend configs are stored in [`terraform/backends`](https://github.com/2i2c-org/pilot-hubs/tree/master/terraform/backends) and can be used by running `terraform init -backend-config=backends/NAME_OF_CHOSEN_BACKEND`.
For example, for our Pangeo projects, run:

```bash
terraform init -backend-config=backends/pangeo-backend.hcl
```
