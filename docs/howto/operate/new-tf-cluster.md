# Add a new GKE cluster managed by our Terraform configuration

This giude will walk through the process of adding a new cluster to our [terraform configuration](https://github.com/2i2c-org/pilot-hubs/tree/master/terraform).

## Cluster Design

This guide will assume you have already followed the guidance in {ref}`/topic/cluster-design` to select the appropriate infrastructure.

## Creating a Terraform variables file for the cluster

The first step is to create a `.tfvars` file in the [`terraform/projects` directory](https://github.com/2i2c-org/pilot-hubs/tree/master/terraform/projects).
Give it a descriptive name that at a glance provides context to the location and/or purpose of the cluster.

The _minimum_ inputs this file requires are:

- `prefix`: Prefix for all objects created by terraform.
  Primary identifier to 'group' together resources.
- `project_id`: GCP Project ID to create resources in.
  Should be the id, rather than display name of the project.

See the [variables file](https://github.com/2i2c-org/pilot-hubs/blob/master/terraform/variables.tf) for other inputs this file can take and their descriptions.

Example `.tfvars` file:

```
prefix     = "my-awesome-project"
project_id = "my-awesome-project-id
```

## Initialising Terraform

The terraform state is located centrally in our `two-eye-two-see-org` GCP project, therefore you must authenticate `gcloud` to your `@2i2c.org` account before initialising terraform.

```bash
gcloud auth login
gcloud auth application-default login
```

Then you can change into the terraform directory and initialise

```bash
cd terraform
terraform init
```

````{note}
If you are deploying a cluster to a project you have access to via a different account, such as a university-affliated account, there are a few extra steps to take.
Hopefully, this will be a rare scenario.

First, you will need to provide terraform with an [access token](https://www.terraform.io/docs/language/settings/backends/gcs.html#configuration-variables) to use the state files.
You can generate one using the below commands and logging in with your 2i2c.org account.

```bash
gcloud auth application-default login
gcloud auth application-default print-acces-token
```

Add the access token to the [terraform backend block](https://github.com/2i2c-org/pilot-hubs/blob/2ef8a4bf35bb5ee9bf04ab3db1218b8c183c5da2/terraform/main.tf#L2-L5) in `main.tf`.
**DO NOT COMMIT THIS CHANGE.**
Then run `terraform init` or `terraform init -reconfigure`.

You can now login to your other gcloud account and proceed with the guide.
````

## Creating a new terraform workspace

We use terraform workspaces so that the state of one `.tfvars` file does not influence another.
Create a new workspace with the below command, and again give it the same name as the `.tfvars` filename.

```bash
terraform workspace new WORKSPACE_NAME
```

## Plan and Apply Changes

```{note}
Make sure the [Artifact Registry API](https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com) in enabled on the project before deploying!
```

Plan your changes with the `terraform plan` command, passing the `.tfvars` file as a variable file.

```bash
terraform plan -var-file=projects/CLUSTER.tfvars
```

Check over the output of this command to ensure nothing if being created/deleted than you expected.
You might want to ask a fellow 2i2c engineer to glance over it too to double check.

If you're satisfied with the plan, apply the changes to deploy the cluster.

```bash
terraform apply -var-file=projects/CLUSTER.tfvars
```

Congratulations, you've just deployed a new cluster!
