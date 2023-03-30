(new-cluster:new-cluster)=
# New Kubernetes cluster on GCP or Azure

This guide will walk through the process of adding a new cluster to our [terraform configuration](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform).

You can find out more about terraform in [](/topic/infrastructure/terraform) and their [documentation](https://www.terraform.io/docs/index.html).

```{attention}
Currently, we do not deploy clusters to AWS _solely_ using terraform.
Please see [](new-cluster:aws) for AWS-specific deployment guidelines.
```

## Cluster Design

This guide will assume you have already followed the guidance in [](/topic/infrastructure/cluster-design) to select the appropriate infrastructure.

## Create a Terraform variables file for the cluster

The first step is to create a `.tfvars` file in the appropriate terraform projects subdirectory:

- [`terraform/gcp/projects`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/projects) for Google Cloud clusters
- [`terraform/azure/projects`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure/projects) for Azure clusters

Give it a descriptive name that at a glance provides context to the location and/or purpose of the cluster.

`````{tab-set}
````{tab-item} Google Cloud
:sync: gcp-key
The _minimum_ inputs this file requires are:

- `prefix`: Prefix for all objects created by terraform.
  Primary identifier to 'group' together resources.
- `project_id`: GCP Project ID to create resources in.
  Should be the id, rather than display name of the project.
- `regional_cluster`: Set to true to provision a [GKE Regional
  Highly Available cluster](https://cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters).
  Costs ~70$ a month, but worth it for the added reliability for most
  cases except when cost saving is an absolute requirement. Defaults
  to `true`.
- `zone`: Zone where cluster nodes and filestore for home directory
  are created.
- `region`: Region where cluster master (if `regional_cluster` is
  `true`) is run, as well as any storage buckets created with
  `user_buckets`.

See the [variables file](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/variables.tf) for other inputs this file can take and their descriptions.

Example `.tfvars` file:

```
prefix           = "my-awesome-project"
project_id       = "my-awesome-project-id"
zone             = "us-central1-c"
region           = "us-central1"
regional_cluster = true
```
````

````{tab-item} Azure
:sync: azure-key
The _minimum_ inputs this file requires are:

- `subscription_id`: Azure subscription ID to create resources in.
  Should be the id, rather than display name of the project.
- `resourcegroup_name`: The name of the Resource Group to be created by terraform, where the cluster and other resources will be deployed into.
- `global_container_registry_name`: The name of an Azure Container Registry to be created by terraform to use for our image.
  This must be unique across all of Azure.
  You can use the following [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) command to check your desired name is available:

  ```bash
  az acr check-name --name ACR_NAME --output table
  ```

- `global_storage_account_name`: The name of a storage account to be created by terraform to use for Azure File Storage.
  This must be unique across all of Azure.
  You can use the following [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) command to check your desired name is available:

  ```bash
  az storage account check-name --name STORAGE_ACCOUNT_NAME --output table
  ```

- `ssh_pub_key`: The public half of an SSH key that will be authorised to login to nodes.

See the [variables file](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure/variables.tf) for other inputs this file can take and their descriptions.

```{admonition} Naming Convention Guidelines for Container Registries and Storage Accounts

Names for Azure container registries and storage accounts **must** conform to the following guidelines:

- alphanumeric strings between 5 and 50 characters for [container registries](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules#microsoftcontainerregistry), e.g., `myContainerRegistry007`
- lowercase letters and numbers strings between 2 and 24 characters for [storage accounts](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules#microsoftstorage), e.g., `mystorageaccount314`
```

```{note}
A failure will occur if you try to create a storage account whose name is not entirely lowercase.
```

We recommend the following conventions using `lowercase`:

- `{CLUSTER_NAME}hubregistry` for container registries
- `{CLUSTER_NAME}hubstorage` for storage accounts

```{note}
Changes in Azure's own requirements might break our recommended convention. If any such failure occurs, please signal it.
```

This increases the probability that we won't take up a namespace that may be required by the Hub Community, for example, in cases where we are deploying to Azure subscriptions not owned/managed by 2i2c.

Example `.tfvars` file:

```
subscription_id                = "my-awesome-subscription-id"
resourcegroup_name             = "my-awesome-resource-group"
global_container_registry_name = "myawesomehubregistry"
global_storage_account_name    = "myawesomestorageaccount"
ssh_pub_key                    = "ssh-rsa my-public-ssh-key"
```
````
`````

Once you have created this file, open a Pull Request to the [`infrastructure` repo](https://github.com/2i2c-org/infrastructure) for review.
See our [review and merge guidelines](infrastructure:review) for how this process should pan out.

## Initialising Terraform

Our default terraform state is located centrally in our `two-eye-two-see-org` GCP project, therefore you must authenticate `gcloud` to your `@2i2c.org` account before initialising terraform.
The terraform state includes **all** cloud providers, not just GCP.

```bash
gcloud auth application-default login
```

Then you can change into the terraform subdirectory for the appropriate cloud provider and initialise terraform.

`````{tab-set}
````{tab-item} Google Cloud
:sync: gcp-key
```bash
cd terraform/gcp
terraform init -backend-config=backends/default-backend.hcl -reconfigure
```
````

````{tab-item} Azure
:sync: azure-key
```bash
cd terraform/azure
terraform init
```
````
`````

````{note}
There are other backend config files stored in `terraform/backends` that will configure a different storage bucket to read/write the remote terraform state for projects which we cannot access from GCP with our `@2i2c.org` email accounts.
This saves us the pain of having to handle multiple authentications as these storage buckets are within the project we are trying to deploy to.

For example, to work with Pangeo you would initialise terraform like so:

```bash
terraform init -backend-config=pangeo-backend.hcl -reconfigure
```

<!-- TODO: add instructions on how/when to create other backends -->
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
When deploying to Google Cloud, make sure the [Compute Engine](https://console.cloud.google.com/apis/library/compute.googleapis.com), [Kubernetes Engine](https://console.cloud.google.com/apis/library/container.googleapis.com), [Artifact Registry](https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com), and [Cloud Logging](https://console.cloud.google.com/apis/library/logging.googleapis.com) APIs are enabled on the project before deploying!
```

First, make sure you are in the new workspace that you just created.

```bash
terraform workspace show
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

Then, output the credentials created by terraform to a file under the appropriate cluster directory: `/config/clusters/$CLUSTER_NAME`.

````{note}
Create the cluster directory if it doesn't already exist with:

```bash
export CLUSTER_NAME=<cluster-name>
```

```bash
mkdir -p ../../config/clusters/$CLUSTER_NAME
```
````

`````{tab-set}
````{tab-item} Google Cloud
:sync: gcp-key
```bash
terraform output -raw ci_deployer_key > ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
```
````

````{tab-item} Azure
:sync: azure-key
```bash
terraform output -raw kubeconfig > ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.yaml
```
````
`````

Then encrypt the key using `sops`.

```{note}
You must be logged into Google with your `@2i2c.org` account at this point so `sops` can read the encryption key from the `two-eye-two-see` project.
```

```bash
cd ../..  # Make sure you are in the root of the repository
sops --output config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.{{ json | yaml }} --encrypt config/clusters/$CLUSTER_NAME/deployer-credentials.secret.{{ json | yaml }}
```

This key can now be committed to the `infrastructure` repo and used to deploy and manage hubs hosted on that cluster.

## Create a `cluster.yaml` file

```{seealso}
We use `cluster.yaml` files to describe a specific cluster and all the hubs deployed onto it.
See [](config:structure) for more information.
```

Create a `cluster.yaml` file under the `config/cluster/$CLUSTER_NAME>` folder and populate it with the following info:

`````{tab-set}
````{tab-item} Google Cloud
:sync: gcp-key
```yaml
name: <cluster-name>  # This should also match the name of the folder: config/clusters/$CLUSTER_NAME>
provider: gcp
gcp:
  # The location of the *encrypted* key we exported from terraform
  key: enc-deployer-credentials.secret.json
  # The name of the GCP project the cluster is deployed in
  project: <gcp-project-name>
  # The name of the cluster *as it appears in the GCP console*! Sometimes our
  # terraform code appends '-cluster' to the 'name' field, so double check this.
  cluster: <cluster-name-in-gcp>
  # The GCP zone the cluster in deployed in. For multi-regional clusters, you
  # may have to strip the last identifier, i.e., 'us-central1-a' becomes 'us-central1'
  zone: <gcp-zone>
  billing:
   # Set to true if billing for this cluster is paid for by the 2i2c card
   paid_by_us: true
   bigquery:
    # contains information about bigquery billing export (https://cloud.google.com/billing/docs/how-to/export-data-bigquery)
    # for calculating how much this cluster costs us. Required if `paid_by_us` is
    # set to true.
    project: <id-of-gcp-project-where-bigquery-dataset-lives>
    dataset: <id-of-bigquery-dataset>
    billing_id: <id-of-billing-account-associated-with-this-project>
```

### Billing information

For projects where we are paying the cloud bill & then passing costs through, you need to fill
in information under` gcp.billing.bigquery` and set `gcp.billing.paid_by_us` to `true`. Partnerships
should be able to tell you if we are doing cloud costs pass through or not, and eventually this should
be provided by a single source of truth for all contracts.

1. Going to the [Billing Tab](https://console.cloud.google.com/billing/linkedaccount) on Google Cloud Console
2. Make sure the correct project is selected in the top bar. You might have to select the 'All' tab in the
   project chooser if you do not see the project right away.
3. Click 'Go to billing account'
4. In the default view (Overview) that opens, you can find the value for `billing_id` in the right sidebar,
   under "Billing Account". It should be of the form `XXXXXX-XXXXXX-XXXXXX`.
5. Select "Billing export" on the left navigation bar, and you will find the values for `project` and
   `dataset` under "Detailed cost usage".
6. If "Detailed cost usage" is not set up, you should [enable it](new-gcp-project:billing-export)
````
````{tab-item} Azure (kubeconfig)
:sync: azure-key
```{warning}
We use this config only when we do not have permissions on the Azure subscription
to create a [Service Principal](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
with terraform.
```
```yaml
name: <cluster-name>  # This should also match the name of the folder: config/clusters/$CLUSTER_NAME
provider: kubeconfig
kubeconfig:
  # The location of the *encrypted* key we exported from terraform
  file: enc-deployer-credentials.secret.yaml
```
````
````{tab-item} Azure (Service Principal)
```yaml
name: <cluster-name>  # This should also match the name of the folder: config/clusters/$CLUSTER_NAME
provider: azure
azure:
  # The location of the *encrypted* key we exported from terraform
  key: enc-deployer-credentials.secret.json
  # The name of the cluster *as it appears in the Azure Portal*! Sometimes our
  # terraform code adjusts the contents of the 'name' field, so double check this.
  cluster: <cluster-name>
  # The name of the resource group the cluster has been deployed into. This is
  # the same as the resourcegroup_name variable in the .tfvars file.
  resource_group: <resource-group-name>
```
````
`````

Commit this file to the repo.

## Adding the new cluster to CI/CD

To ensure the new cluster is appropriately handled by our CI/CD system, please add it as an entry in the following places:

- The [`deploy-hubs.yaml`](https://github.com/2i2c-org/infrastructure/blob/008ae2c1deb3f5b97d0c334ed124fa090df1f0c6/.github/workflows/deploy-hubs.yaml#L121) workflow file
