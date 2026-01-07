(topic:terraform)=
# Terraform

[Terraform](https://www.terraform.io/) is used to manage our infrastructure in the cloud.
We use completely different terraform code for each cloud provider, under `terraform/<cloud-provider>`.
This is much simpler than trying to abstract them away into a 'lowest common denominator' set of modules.

The source files for each provider we currently deploy with terraform are under a specific
directory under `terraform/` in our [`infrastructure` repo](https://github.com/2i2c-org/infrastructure).

Each provider directory also has a `projects` subdirectory where variables defining each cluster are stored.

## State and Backends
Terraform stores [state](https://developer.hashicorp.com/terraform/language/state) to
reflect the *current state* of the infrastructure managed, so it can figure out what
changes need to happen and how to make them happen. This state has to be stored somewhere,
and we store it in a [Google Cloud Storage Bucket](https://developer.hashicorp.com/terraform/language/backend/gcs)
by default. The configuration is specified directly in `main.tf` for each cloud provider.

In some cases, we may want to store the state in a different place, primarily so that
communities can run `terraform apply` themselves without being given access to *every*
community's terraform state. See [the documentation for community partners](contributing:community-partner:terraform) for more details.

### Backend Initialization

To initialize the backends, you need to run `terraform init` command from within the directory where the source files of the specific provider you want to access are.

Example:

```bash
cd terraform/azure
terraform init
```

```{note}
If prior backend data exists in a `terraform.lock.hcl`, you might see an `Error: Backend configuration changed` when trying to initialize that backend. To reconfigure this backend, ignoring any saved configuration, add the `-reconfigure` flag to the init command.
```

If you're trying to work on a project that has state stored elsewhere, [follow the docs here](contributing:community-partner:terraform)

(topic:terraform:workspaces)=
## Workspaces

We use [terraform workspaces](https://www.terraform.io/docs/language/state/workspaces.html)
to maintain separate terraform states about different clusters we manage.
There should be one workspace per cluster, with the same name as the `.tfvars`
file with variable definitions for that cluster.

```{note}
Workspaces are defined **per backend**.
If you can't find the workspace you're looking for, double check you've initialized the correct backend.
```

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
terraform init
```
````
