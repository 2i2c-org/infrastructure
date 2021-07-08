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

## Creating a new terraform workspace

We use terraform workspaces so that the state of one `.tfvars` file does not influence another.
Create a new workspace with the below command, and again give it a descriptive name, perhaps even the same as the `.tfvars` filename.

```bash
terraform workspace new WORKSPACE_NAME
```

## Plan and Apply Changes
