(topic:terraform)=
# Terraform

[Terraform](https://www.terraform.io/) is used to manage our infrastructure in the cloud.
We use completely different terraform code for each cloud provider, under `terraform/<cloud-provider>`.
This is much simpler than trying to abstract them away into a 'lowest common denominator' set of modules.

The source files for each provider we currently deploy with terraform are under the following directories in our [`infrastructure` repo](https://github.com/2i2c-org/infrastructure):

- [`terraform/gcp`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp)
- [`terraform/azure`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure)
- [`terraform/aws`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/aws)

Each provider directory also has a `projects` subdirectory where variables defining each cluster are stored.

## Backends

A [backend](https://www.terraform.io/language/settings/backends/configuration) defines where Terraform stores its state data files in cloud storage (we use a GCP bucket for the majority of our deployments).
Normally, we are using Terraform when logged in with our 2i2c accounts and there's no need to explicitly define a backend.

But for some projects where we don't have access to using our 2i2c accounts, e.g. universities that require us to have specific university-affiliated identities, we can configure different backends to access the terraform state stored in those projects.
Working this way saves us the pain of trying to work with terraform using two different authentications.

These backend configs are stored in [`terraform/gcp/backends`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/backends).
Currently, we only implement a choice of backend for GCP deployments.

### Backend Initialization

To initialize the backends, you need to run `terraform init` command from within the directory where the source files of the specific provider you want to access are.

Example:

```bash
cd terraform/azure
terraform init
```

````{note}
Currently, since our GCP terraform config is the only one that uses different backends, an extra `-backend-config` flag needs to be passed to the `init` command to initialize.

For example, for our Pangeo projects, run:

```bash
cd terraform/gcp
terraform init -backend-config=backends/pangeo-backend.hcl
```
````

```{note}
If prior backend data exists in a `terraform.lock.hcl`, you might see an `ERROR` when trying to initialize that backend. To reconfigure this backend, ignoring any saved configuration, add the `-reconfigure` flag to the init command.
```

## Workspaces

We use [terraform workspaces](https://www.terraform.io/docs/language/state/workspaces.html)
to maintain separate terraform states about different clusters we manage.
There should be one workspace per cluster, with the same name as the `.tfvars`
file with variable definitions for that cluster.

```{note}
Workspaces are defined **per backend**.
If you can't find the workspace you're looking for, double check you've enabled the correct backend.
```

Workspaces are stored centrally in the `two-eye-two-see` GCP project, even
when we use Terraform for projects running on AWS / Azure. You must have
access to this project before you can use terraform for our infrastructure.

## How to change Terraform workspaces

### If the new workspace is stored in the same backend as the current workspace

If you want to change to a different terraform workspace that is stored in the same backend that you initialised with, you can simply run:

```bash
terraform workspace select WORKSPACE_NAME
```


:::{note}
We recently renamed the `pilot-hubs` repository to `infrastructure`, however we have not yet renamed the Terraform projects, so they are still named `pilot-hubs`!
:::

For example, if you were working in the `pilot-hubs` workspace but want to change to `justiceinnovationlab`, these are both stored in the same backend and so the command looks like:

```bash
terraform workspace select justiceinnovationlab
```

````{note}
For the majority of day-to-day work, this will be the prevalent workflow provided you have initialised terraform with

```bash
terraform init -backend-config=backends/default-backend.hcl -reconfigure
```
````

### If the new workspace is stored in a different backend to the current workspace

To change between workspaces that are stored in _different_ backends, terraform will need to be reinitialised in order to pick up the new backend.
The commands, therefore, are:

```bash
terraform init -backend-config=backends/<REQUIRED_CONFIG>.hcl -reconfigure
terraform workspace select WORKSPACE_NAME
```

For example, if you were working on our `pilot-hubs`, with our default backend initialised, but wanted to change to working on our Pangeo deployments, the commands would look as follows:

```bash
terraform init -backend-config=backends/pangeo-backend.hcl -reconfigure
terraform workspace select pangeo-hubs
```
