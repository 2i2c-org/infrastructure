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
terraform init -backend-config=backends/default-backend.hcl -reconfigure
```

```{note}
Workspaces are defined **per backend**.
If you can't find the workspace you're looking for, double check you've enabled the correct backend.
```

## Other remote state storage

For some projects where we don't have access to using our 2i2c accounts, e.g. universities that require us to have specific university-affiliated identities, we can configure different backends to access the terraform state stored in those projects.
Working this way saves us the pain of trying to work with terraform using two different authentications.
The backend configs are stored in [`terraform/backends`](https://github.com/2i2c-org/infrastructure/tree/master/terraform/backends) and can be used by running `terraform init -backend-config=backends/NAME_OF_CHOSEN_BACKEND -reconfigure`.
For example, for our Pangeo projects, run:

```bash
terraform init -backend-config=backends/pangeo-backend.hcl -reconfigure
```

## How to switch Terraform workspaces

### If the new workspace is stored in the same backend as the current workspace

If you want to switch to a different terraform workspace that is stored in the same backend that you initialised with, you can simply run:

```bash
terraform workspace switch WORKSPACE_NAME
```

For example, if you were working in the `infrastructure` workspace but want to switch to `justiceinnovationlab`, these are both stored in the same backend and so the command looks like:

```bash
terraform workspace switch justiceinnovationlab
```

````{note}
For the majority of day-to-day work, this will be the prevalent workflow provided you have initialised terraform with

```bash
terraform init -backend-config=backends/default-backend.hcl -reconfigure
```
````

### If the new workspace is stored in a different backend to the current workspace

To switch between workspaces that are stored in _different_ backends, terraform will need to be reinitialised in order to pick up the new backend.
The commands, therefore, are:

```bash
terraform init -backend-config=backends/<REQUIRED_CONFIG>.hcl -reconfigure
terraform workspace select WORKSPACE_NAME
```

For example, if you were working on our `infrastructure`, with our default backend initialised, but wanted to switch to working on our Pangeo deployments, the commands would look as follows:

```bash
terraform init -backend-config=backends/pangeo-backend.hcl -reconfigure
terraform workspace select pangeo-hubs
```
## Cloud provider abstractions

We will use completely different terraform code for each cloud provider,
under `terraform/<cloud-provider>`. This is much simpler than trying to abstract
them away into a 'lowest common denominator' set of modules.
