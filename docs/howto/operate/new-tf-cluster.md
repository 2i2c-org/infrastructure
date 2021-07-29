# Add a new GKE cluster managed by our Terraform configuration

This guide will walk through the process of adding a new cluster to our [terraform configuration](https://github.com/2i2c-org/pilot-hubs/tree/master/terraform).

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

Once you have created this file, open a Pull Request to the `pilot-hubs` repo for review.

## Initialising Terraform

Our default terraform state is located centrally in our `two-eye-two-see-org` GCP project, therefore you must authenticate `gcloud` to your `@2i2c.org` account before initialising terraform.

```bash
gcloud auth application-default login
```

Then you can change into the terraform directory and initialise

```bash
cd terraform
terraform init -backend-config=backends/default-backend.hcl
```

````{note}
If you are working on a project which you cannot access with your 2i2c account, there are other backend config files stored in `terraform/backends` that will configure a different storage bucket to read/write the remote terraform state.
This saves us the pain of having to handle multiple authentications as these storage buckets are within the project we are trying to deploy to.

For example, to work with Pangeo you would initialise terraform like so:

```bash
terraform init -backend-config=pangeo-backend.hcl
```
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
Copy-paste the plan into your open Pull Request so a fellow 2i2c engineer can double check it too.

If you're both satisfied with the plan, merge the Pull Request and apply the changes to deploy the cluster.

```bash
terraform apply -var-file=projects/CLUSTER.tfvars
```

Congratulations, you've just deployed a new cluster!

## Exporting and Encrypting the Continuous Deployment Service Account

To begin deploying and operating hubs on your new cluster, we need to export the Continuous Deployment Service Account created by terraform, encrypt it using `sops`, and store it in the `secrets` directory of the `pilot-hubs` repo.

Check you are still in the correct terraform workspace

```bash
terraform workspace show
```

If you need to change, you can do so as follows

```bash
terraform workspace list  # List all available workspaces
terraform workspace select WORKSPACE_NAME
```

Then, output the JSON key for the service account created by terraform to a file under the `secrets` directory.

```bash
terraform output -raw ci_deployer_key > ../secrets/CLUSTER_NAME.json
```

where `CLUSTER_NAME` matches the name of our `.tfvars` file.

Encrypt the key using `sops`

```{note}
You must be logged into Google with your `@2i2c.org` account at this point so `sops` can read the encryption key from the `two-eye-two-see` project.
```

```bash
cd ..
sops --encrypt --in-place secrets/CLUSTER_NAME.json
```

This key can now be committed to the `pilot-hubs` repo and used to deploy and manage hubs hosted on that cluster.
