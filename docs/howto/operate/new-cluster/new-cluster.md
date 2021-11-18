(new-cluster:new-cluster)=
# Add a new Kubernetes cluster

This guide will walk through the process of adding a new cluster to our [terraform configuration](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform).

```{attention}
Currently, we do not deploy clusters to AWS using terraform.
Please see [](new-cluster:aws) for AWS-specific deployment guidelines.
```

## Cluster Design

This guide will assume you have already followed the guidance in [](/topic/cluster-design) to select the appropriate infrastructure.

## Create a Terraform variables file for the cluster

The first step is to create a `.tfvars` file in the appropriate terraform projects subdirectory:

- [`terraform/gcp/projects`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/projects) for Google Cloud clusters
- [`terraform/azure/projects`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure/projects) for Azure clusters

Give it a descriptive name that at a glance provides context to the location and/or purpose of the cluster.

````{tabbed} Google Cloud
The _minimum_ inputs this file requires are:

- `prefix`: Prefix for all objects created by terraform.
  Primary identifier to 'group' together resources.
- `project_id`: GCP Project ID to create resources in.
  Should be the id, rather than display name of the project.

See the [variables file](https://github.com/2i2c-org/infrastructure/blob/HEAD/terraform/gcp/variables.tf) for other inputs this file can take and their descriptions.

Example `.tfvars` file:

```
prefix     = "my-awesome-project"
project_id = "my-awesome-project-id
```
````

````{tabbed} Azure
The _minimum_ inputs this file requires are:

- `subscription_id`: Azure subscription ID to create resources in.
  Should be the id, rather than display name of the project.
- `resourcegroup_name`: The name of the Resource Group that the cluster and other resources will be deployed into.
- `global_container_registry_name`: The name of an Azure Container Registry to use for our image.
  This must be unique across all of Azure.
  You can use the following command to check your desired name is available:

  ```bash
  az acr check-name --name ACR_NAME --output table
  ```

- `global_storage_account_name`: The name of a storage account to use for Azure File Storage.
  This must be unique across all of Azure.
  You can use the following command to check your desired name is available:

  ```bash
  az storage account check-name --name STORAGE_ACCOUNT_NAME --output table
  ```

- `ssh_pub_key`: The public half of an SSH key that will be authorised to login to nodes.

See the [variables file](https://github.com/2i2c-org/infrastructure/blob/HEAD/terraform/azure/variables.tf) for other inputs this file can take and their descriptions.

```{admonition} Naming Convention Guidelines for Container Registries and Storage Accounts

Names for Azure container registries and storage accounts **must** conform to the following guidelines:

- alphanumeric strings between 5 and 50 characters for [container registries](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules#microsoftcontainerregistry), e.g., `myContainerRegistry007`
- alphanumeric strings between 2 and 24 characters for [storage accounts](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules#microsoftstorage), e.g., `myStorageAccount314`

We explictly recommend the following conventions using `lowerCamelCase`:

- `{CLUSTER_NAME}HubRegistry` for container registries
- `{CLUSTER_NAME}HubStorage` for storage accounts

This increases the probability that we won't take up a namespace that may be required by the Hub Community, for example, in cases where we are deploying to Azure subscriptions not owned/managed by 2i2c.
```

Example `.tfvars` file:

```
subscription_id                = "my-awesome-subscription-id"
resourcegroup_name             = "my-awesome-resource-group"
global_container_registry_name = "myawesomecontainerregistry"
global_storage_account_name    = "myawesomestorageaccount"
ssh_pub_key                    = "ssh-rsa my-public-ssh-key"
```
````

Once you have created this file, open a Pull Request to the [`infrastructure` repo](https://github.com/2i2c-org/infrastructure) for review.
See our [review and merge guidelines](infrastructure:review) for how this process should pan out.

## Initialising Terraform

Our default terraform state is located centrally in our `two-eye-two-see-org` GCP project, therefore you must authenticate `gcloud` to your `@2i2c.org` account before initialising terraform.
The terraform state includes **all** cloud providers, not just GCP.

```bash
gcloud auth application-default login
```

Then you can change into the terraform subdirectory for the appropriate cloud provider and initialise terraform.

```bash
cd terraform/{{ gcp | azure }}
terraform init -backend-config=backends/default-backend.hcl -reconfigure
```

````{note}
If you are working on a project which you cannot access with your 2i2c account, there are other backend config files stored in `terraform/backends` that will configure a different storage bucket to read/write the remote terraform state.
This saves us the pain of having to handle multiple authentications as these storage buckets are within the project we are trying to deploy to.

For example, to work with Pangeo you would initialise terraform like so:

```bash
terraform init -backend-config=pangeo-backend.hcl -reconfigure
```
````

## Creating a new terraform workspace

We use terraform workspaces so that the state of one `.tfvars` file does not influence another.
Create a new workspace with the below command, and again give it the same name as the `.tfvars` filename.

```bash
terraform workspace new WORKSPACE_NAME
```

```{note}
Workspaces are defined **per backend**.
If you can't find the workspace you're looking for, double check you've enabled the correct backend.
```

## Plan and Apply Changes

```{note}
When deploying to Google Cloud, make sure the [Artifact Registry API](https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com) is enabled on the project before deploying!
```

Plan your changes with the `terraform plan` command, passing the `.tfvars` file as a variable file.

```bash
terraform plan -var-file=projects/CLUSTER.tfvars
```

Check over the output of this command to ensure nothing is being created/deleted that you didn't expect.
Copy-paste the plan into your open Pull Request so a fellow 2i2c engineer can double check it too.

If you're both satisfied with the plan, merge the Pull Request and apply the changes to deploy the cluster.

```bash
terraform apply -var-file=projects/CLUSTER.tfvars
```

Congratulations, you've just deployed a new cluster!

## Exporting and Encrypting the Cluster Access Credentials

To begin deploying and operating hubs on your new cluster, we need to export the credentials created by terraform, encrypt it using `sops`, and store it in the `secrets` directory of the `infrastructure` repo.

Check you are still in the correct terraform workspace

```bash
terraform workspace show
```

If you need to change, you can do so as follows

```bash
terraform workspace list  # List all available workspaces
terraform workspace select WORKSPACE_NAME
```

Then, output the credentials created by terraform to a file under the `secrets` directory.

````{tabbed} Google Cloud
```bash
terraform output -raw ci_deployer_key > ../../secrets/CLUSTER_NAME.json
```
````

````{tabbed} Azure
```bash
terraform output -raw kubeconfig > ../../secrets/CLUSTER_NAME.yaml
```
````

where `CLUSTER_NAME` matches the name of our `.tfvars` file.

Then encrypt the key using `sops`.

```{note}
You must be logged into Google with your `@2i2c.org` account at this point so `sops` can read the encryption key from the `two-eye-two-see` project.
```

```bash
cd ..
sops --encrypt --in-place secrets/CLUSTER_NAME.json
```

This key can now be committed to the `infrastructure` repo and used to deploy and manage hubs hosted on that cluster.
