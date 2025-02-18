(new-cluster:new-cluster)=
# New Kubernetes cluster on GCP, Azure or AWS

This guide will walk through the process of adding a new cluster to our [terraform configuration](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform).

You can find out more about terraform in [](/topic/infrastructure/terraform) and their [documentation](https://www.terraform.io/docs/index.html).

```{attention}
Currently, we do not deploy clusters to AWS _solely_ using terraform.
We use [eksctl](https://eksctl.io/) to provision our k8s clusters on AWS and
terraform to provision supporting infrastructure, such as storage buckets.
```

## Cluster Design

This guide will assume you have already followed the guidance in [](/topic/infrastructure/cluster-design) to select the appropriate infrastructure.

(new-cluster:prerequisites)=
## Prerequisites

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
1. Install `kubectl`, `helm`, `sops`, etc.

   In [](tutorials:setup) you find instructions on how to setup `sops` to
   encrypt and decrypt files.

2. Install [`aws`](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-instructions)

   Verify install and version with `aws --version`. You should have at least
   version 2.

3. Install or upgrade [eksctl](https://eksctl.io/introduction/#installation)

   Mac users with homebrew can run `brew install eksctl`.

   Verify install and version with `eksctl version`. You should have *the latest
   version* of this CLI.

   ```{important}
   Without the latest version, you may install an outdated versions of `aws-node`
   because [its hardcoded](https://github.com/eksctl-io/eksctl/pull/7756).
   ```

4. Install [`jsonnet`](https://github.com/google/jsonnet)

   Mac users with homebrew can run `brew install jsonnet`.

   Verify install and version with `jsonnet --version`.
````

````{tab-item} Google Cloud
:sync: gcp-key
1. Install `kubectl`, `helm`, `sops`, etc.

   In [](tutorials:setup) you find instructions on how to setup `sops` to
   encrypt and decrypt files.
````

````{tab-item} Azure
:sync: azure-key
1. Install `kubectl`, `helm`, `sops`, etc.

   In [](tutorials:setup) you find instructions on how to setup `sops` to
   encrypt and decrypt files.
````

````{tab-item} Jetstream2
:sync: jetstream2-key
1. Install `kubectl`, `helm`, `sops` and pip install `python-openstackclient` and `python-magnumclient`

   In [](tutorials:setup) you find instructions on how to setup `sops` to
   encrypt and decrypt files.
````
`````

## Create a new cluster

### Setup credentials

``````{tab-set}

````{tab-item} AWS
:sync: aws-key
Depending on whether this project is using AWS SSO or not, you can use the following
links to figure out how to authenticate to this project from your terminal.

- [For accounts setup with AWS SSO](cloud-access:aws-sso:terminal)
- [For accounts without AWS SSO](cloud-access:aws-iam:terminal)
````

````{tab-item} Google Cloud
:sync: gcp-key
N/A
````

````{tab-item} Azure
:sync: azure-key
N/A
````

````{tab-item} Jetstream2
:sync: jetstream2-key

You will need to generate Jetstream2 application credentials that the cli client will use to authenticate against the desired Jetstream2 allocation.

There is a comprehensive guide on how to generate the credentials, and export them as environment variables through sourcing an `openrc.sh` file. It is important to note that when creating the application credentials you must give them `UNRESTRICTED` access by ticking the corresponding box and also select all roles available to you in the `ROLES` box.

- Go to https://js2.jetstream-cloud.org/ and follow the guide at https://cvw.cac.cornell.edu/jetstreamapi/cli/openrc, **but keep in mind the `UNRESTRICTED` part as that's not covered in the guide.**
- After exporting the variables in the openrc.sh file, make sure you have access by running:
     ```
     openstack coe cluster list
     ```
`````
``````

(new-cluster:generate-cluster-files)=
### Generate cluster files

We automatically generate the files required to setup a new cluster:

`````{tab-set}

````{tab-item} AWS
:sync: aws-key
- A `.jsonnet` file for use with `eksctl`
- A `sops` encrypted [ssh key](https://eksctl.io/introduction/#ssh-access) that can be used to ssh into the kubernetes nodes.
- A ssh public key used by `eksctl` to grant access to the private key.
- A `.tfvars` terraform variables file that will setup most of the non EKS infrastructure.
- The cluster config directory in `./config/cluster/<new-cluster>`
- The `cluster.yaml` config file
- The support values file `support.values.yaml`
- The the support credentials encrypted file `enc-support.values.yaml` 
````

````{tab-item} Google Cloud
:sync: gcp-key
- A `.tfvars` file for use with `terraform`
- The cluster config directory in `./config/cluster/<new-cluster>`
- A sample `cluster.yaml` config file
- The support values file `support.values.yaml`
- The the support credentials encrypted file `enc-support.values.yaml` 
````

````{tab-item} Azure
:sync: azure-key
```{warning}
An automated deployer command doesn't exist yet, these files need to be manually generated!
```
````

````{tab-item} Jetstream2
:sync: jetstream2-key
```{warning}
An automated deployer command doesn't exist yet, these files need to be manually generated!
```
````
`````

You can generate these with:

`````{tab-set}
````{tab-item} AWS
:sync: aws-key

```bash
export CLUSTER_NAME=<cluster-name>
export CLUSTER_REGION=<cluster-region-like ca-central-1>
export ACCOUNT_ID=<declare 2i2c for clusters under 2i2c SSO, otherwise an account id or alias>
```

```bash
deployer generate dedicated-cluster aws --cluster-name=$CLUSTER_NAME --cluster-region=$CLUSTER_REGION --account-id=$ACCOUNT_ID
```

### Create and render an eksctl config file

We use an eksctl [config file](https://eksctl.io/usage/schema/) in YAML to specify
how our cluster should be built. Since it can get repetitive, we use
[jsonnet](https://jsonnet.org) to declaratively specify this config. You can
find the `.jsonnet` files for the current clusters in the `eksctl/` directory.

The previous step should've created a baseline `.jsonnet` file you can modify as
you like. The eksctl docs have a [reference](https://eksctl.io/usage/schema/)
for all the possible options. You'd want to make sure to change at least the following:

- Region / Zone - make sure you are creating your cluster in the correct region
  and verify the suggested zones 1a, 1b, and 1c actually are available in that
  region.

  ```bash
  # a command to list availability zones, for example
  # ca-central-1 doesn't have 1c, but 1d instead
  aws ec2 describe-availability-zones --region=$CLUSTER_REGION
  ```
- Size of nodes in instancegroups, for both notebook nodes and dask nodes. In particular,
  make sure you have enough quota to launch these instances in your selected regions.
- Kubernetes version - older `.jsonnet` files might be on older versions, but you should
  pick a newer version when you create a new cluster.

Once you have a `.jsonnet` file, you can render it into a config file that eksctl
can read.

```{tip}
Make sure to run this command inside the `eksctl` directory.
```

```bash
jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
```

```{tip}
The `*.eksctl.yaml` files are git ignored as we can regenerate it, so work
against the `*.jsonnet` file and regenerate the YAML file when needed by a
`eksctl` command.
```

### Create the cluster

Now you're ready to create the cluster!

```{tip}
Make sure to run this command **inside** the `eksctl` directory, otherwise it cannot discover the `ssh-keys` subfolder.
```

```bash
eksctl create cluster --config-file=$CLUSTER_NAME.eksctl.yaml
```

This might take a few minutes.

If any errors are reported in the config (there is a schema validation step),
fix it in the `.jsonnet` file, re-render the config, and try again.

Once it is done, you can test access to the new cluster with `kubectl`, after
getting credentials via:

```bash
aws eks update-kubeconfig --name=$CLUSTER_NAME --region=$CLUSTER_REGION
```

`kubectl` should be able to find your cluster now! `kubectl get node` should show
you at least one core node running.

````

````{tab-item} Google Cloud
:sync: gcp-key
```bash
export CLUSTER_NAME=<cluster-name>
export CLUSTER_REGION=<cluster-region-like ca-central-1>
export PROJECT_ID=<gcp-project-id>
```

```bash
deployer generate dedicated-cluster gcp --cluster-name=$CLUSTER_NAME --project-id=$PROJECT_ID --cluster-region=$CLUSTER_REGION
```
````

````{tab-item} Azure
:sync: azure-key

An automated deployer command doesn't exist yet, these files need to be manually generated. The _minimum_ inputs this file requires are:

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

````{tab-item} Jestream2
:sync: jetstream2-key

An automated deployer command doesn't exist yet, these files need to be manually generated. The _minimum_ inputs this file requires are:

- `prefix`: A prefix that will be added to all the cluster-specific resources. Changing this will force the recreation of all resources.
- `notebook_nodes`: A list of nodebook nodes that will be created in the cluster. The `machine_type` should be one of the [Jetstream2 flavors](https://docs.jetstream-cloud.org/general/instance-flavors/#jetstream2-cpu).

  ```{warning}
  The value of `min` cannot be zero as currently the Magnum API driver doesn't support having any nodepool with zero nodes.
  ```

  ```
  notebook_nodes = {
    "m3.medium" : {
      min : 1,
      max : 100,
      # 8 CPU, 30 RAM
      # https://docs.jetstream-cloud.org/general/instance-flavors/#jetstream2-cpu
      machine_type : "m3.medium",
      labels = {
        "hub.jupyter.org/node-purpose" = "user",
        "k8s.dask.org/node-purpose"    = "scheduler",
      }
    },
  }
  ```
````
`````

## Add GPU nodegroup if needed

If this cluster is going to have GPUs, you should edit the generated jsonnet file
to [include a GPU nodegroups](howto:features:gpu).

## Initialising Terraform

Our default terraform state is located centrally in our `two-eye-two-see-org` GCP project, therefore you must authenticate `gcloud` to your `@2i2c.org` account before initialising terraform.
The terraform state includes **all** cloud providers, not just GCP.

```bash
gcloud auth application-default login
```

Then you can change into the terraform subdirectory for the appropriate cloud provider and initialise terraform.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key

Our AWS *terraform* code is now used to deploy supporting infrastructure for the EKS cluster, including:

- An IAM identity account for use with our CI/CD system
- Appropriately networked EFS storage to serve as an NFS server for hub home directories
- Optionally, setup a [shared database](features:shared-db:aws)
- Optionally, setup [user buckets](howto:features:storage-buckets)

The steps above will have created a default `.tfvars` file. This file can either be used as-is or edited to enable the optional features listed above.

Initialise terraform for use with AWS:

```bash
cd terraform/aws
terraform init
```
````

````{tab-item} Google Cloud
:sync: gcp-key
```bash
cd terraform/gcp
terraform init
```
````

````{tab-item} Azure
:sync: azure-key
```bash
cd terraform/azure
terraform init
```
````

````{tab-item} Jetstream2
:sync: jetstream2-key
```bash
cd terraform/openstack
terraform init
```
````
`````

## Creating a new terraform workspace

We use terraform workspaces so that the state of one `.tfvars` file does not influence another.
Create a new workspace with the below command, and again give it the same name as the `.tfvars` filename, $CLUSTER_NAME.

```bash
terraform workspace new $CLUSTER_NAME
```

```{note}
Workspaces are defined **per backend**.
If you can't find the workspace you're looking for, double check you've enabled the correct backend.
```

## Setting up Budget Alerts

Follow the instructions in [](howto:setting-up-budget-alerts) to determine if and
how you should setup budget alerts.

You can learn more about our budget alerts in [](topic:billing:budget-alerts).

## Plan and Apply Changes

```{important}
When deploying to Google Cloud, make sure the [Compute Engine](https://console.cloud.google.com/apis/library/compute.googleapis.com), [Kubernetes Engine](https://console.cloud.google.com/apis/library/container.googleapis.com), [Artifact Registry](https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com), [Cloud Filestore](https://console.cloud.google.com/apis/library/file.googleapis.com), and [Cloud Logging](https://console.cloud.google.com/apis/library/logging.googleapis.com) APIs are enabled on the project before deploying!
```

First, make sure you are in the new workspace that you just created.

```bash
terraform workspace show
```

Plan your changes with the `terraform plan` command, passing the `.tfvars` file as a variable file.

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
```

Check over the output of this command to ensure nothing is being created/deleted that you didn't expect.
Copy-paste the plan into your open Pull Request so a fellow 2i2c engineer can double check it too.

If you're both satisfied with the plan, merge the Pull Request and apply the changes to deploy the cluster.

```bash
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

Congratulations, you've just deployed a new cluster!

(new-cluster:terraform:cluster-credentials)=
## Exporting and Encrypting the Cluster Access Credentials

In the previous step, we will have created an IAM user with just enough permissions for automatic deployment of hubs from CI/CD. Since these credentials are checked-in to our git repository and made public, they should have least amount of permissions possible.

To begin deploying and operating hubs on your new cluster, we need to export these credentials, encrypt them using `sops`, and store them in the `secrets` directory of the `infrastructure` repo.


1. First, make sure you are in the right terraform directory:

    `````{tab-set}
    ````{tab-item} AWS
    :sync: aws-key
      ```bash
      cd terraform/aws
      ```
    ````

    ````{tab-item} Google Cloud
    :sync: gcp-key
      ```bash
      cd terraform/gcp
      ```
    ````

    ````{tab-item} Azure
    :sync: azure-key
      ```bash
      cd terraform/azure
      ```
    ````

    ````{tab-item} Jetstream2
    :sync: jetstream2-key
      ```bash
      cd terraform/openstack
      ```
    ````
    `````

1. Check you are still in the correct terraform workspace

    ```bash
    terraform workspace show
    ```

    If you need to change, you can do so as follows

    ```bash
    terraform workspace list  # List all available workspaces
    terraform workspace select WORKSPACE_NAME
    ```

1. Fetch credentials for automatic deployment

    Create the directory if it doesn't exist already:
    ```bash
    mkdir -p ../../config/clusters/$CLUSTER_NAME
    ```

    `````{tab-set}
    ````{tab-item} AWS
    :sync: aws-key
      ```bash
      terraform output -raw continuous_deployer_creds > ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
      ```
    ````

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

    ````{tab-item} Jetstream2
    :sync: jetstream2-key
      To access the cluster using kubectl we need to get the kubeconfig with:
      ```bash
        openstack coe cluster config <cluster-name> --force > ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
      ```
      This command will generate a file named config in the cwd with the configuration.
      The --force flag will overwrite this file if it already exists.
    
      Encrypt the kubeconfig file using `sops`:
      ```bash
      sops --output ./config --encrypt ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
      ```

      ```{note}
      You must be logged into Google with your `@2i2c.org` account at this point so `sops` can read the encryption key from the `two-eye-two-see` project.
      ```

      Delete the config file to avoid committing it by mistake:
      ```
      rm ./config
      ```
    ````
    `````

1. Then encrypt the key using `sops`.

    ```{important}
    This step can be skipped for Jetstream2 because the kubeconfig file is already encrypted from step 1.
    ```

    ```{note}
    You must be logged into Google with your `@2i2c.org` account at this point so `sops` can read the encryption key from the `two-eye-two-see` project.
    ```

    ```bash
    sops --output ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json --encrypt ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
    ```

    This key can now be committed to the `infrastructure` repo and used to deploy and manage hubs hosted on that cluster.

1. Double check to make sure that the `config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json` file is actually encrypted by `sops` before checking it in to the git repo. Otherwise this can be a serious security leak!

    ```bash
    cat ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json
    ```

## Create a `cluster.yaml` file

```{seealso}
We use `cluster.yaml` files to describe a specific cluster and all the hubs deployed onto it.
See [](config:structure) for more information.
```

Create a `cluster.yaml` file under the `config/cluster/$CLUSTER_NAME>` folder and populate it with the following info:

`````{tab-set}

````{tab-item} AWS
:sync: aws-key

A `cluster.yaml` file should already have been generated as part of [](new-cluster:generate-cluster-files).
````

````{tab-item} Google Cloud
:sync: gcp-key

A `cluster.yaml` file should already have been generated as part of [](new-cluster:generate-cluster-files).

### Billing information

For projects where we are paying the cloud bill & then passing costs through, you need to fill
in information under `gcp.billing.bigquery` and set `gcp.billing.paid_by_us` to `true`. Partnerships
should be able to tell you if we are doing cloud costs pass through or not.

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

````{tab-item} Jetstream2 (kubeconfig)
:sync: jetstream2-key
```yaml
name: <cluster-name>  # This should also match the name of the folder: config/clusters/$CLUSTER_NAME
provider: kubeconfig
kubeconfig:
  # The location of the *encrypted* key we exported from terraform
  file: enc-deployer-credentials.secret.yaml
```
````
`````

Commit this file to the repo.

## Access

`````{tab-set}
````{tab-item} AWS
:sync: aws-key

### Grant the deployer's IAM user cluster access

```{note}
This still works, but makes use of a deprecated system (`iamidentitymapping` and
`aws-auth` ConfigMap in kube-system namespace) instead of the new system called
[EKS access entries]. Migrating to the new system is [tracked by this github issue](https://github.com/2i2c-org/infrastructure/issues/4558).

[eks access entries]: https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html
```

We need to grant the freshly created deployer IAM user access to the kubernetes cluster.

1. As this requires passing in some parameters that match the created cluster,
  we have a `terraform output` that can give you the exact command to run.

  ```bash
  terraform output -raw eksctl_iam_command
  ```

2. Run the `eksctl create iamidentitymapping` command returned by `terraform output`.
  That should give the continuous deployer user access.

  The command should look like this:

  ```bash
  eksctl create iamidentitymapping \
      --cluster $CLUSTER_NAME \
      --region $CLUSTER_REGION \
      --arn arn:aws:iam::<aws-account-id>:user/hub-continuous-deployer \
      --username hub-continuous-deployer \
      --group system:masters
  ```

  Test the access by running:

  ```bash
  deployer use-cluster-credentials $CLUSTER_NAME
  ```

  and running:

  ```bash
  kubectl get node
  ```

  It should show you the provisioned node on the cluster if everything works out ok.

### Grant cluster access to other users

```{note}
This step is only needed within AWS accounts outside 2i2c's AWS organization where
we haven't logged in using 2i2c SSO.

This is because new EKS clusters comes with an access entry to the _user or role_
that created the cluster, and when we work against an AWS account within the 2i2c
AWS organization, we all assume the same role, so an access entry for that role
grants us all access. However, when we work against AWS accounts outside the 2i2c
AWS organization, we typically use a IAM User directly, and that will be
different for all of us, so we need to add access entries for other engineers as
well then.
```

Find the usernames of the 2i2c engineers on this particular AWS account, and run
the following command to give them access using the deprecated system active in
parallel to the newer system with access entries:

```{note}
You can modify the command output by running `terraform output -raw eksctl_iam_command`
as described in [](new-cluster:terraform:cluster-credentials).
```

```bash
eksctl create iamidentitymapping \
   --cluster $CLUSTER_NAME \
   --region $CLUSTER_REGION \
   --arn arn:aws:iam::<aws-account-id>:user/<iam-user-name> \
   --username <iam-user-name> \
   --group system:masters
```

This gives all the users full access to the entire kubernetes cluster.
After this step is done, they can fetch local config with:

```bash
aws eks update-kubeconfig --name=$CLUSTER_NAME --region=$CLUSTER_REGION
```

This should eventually be converted to use an [IAM Role] instead, so we need not
give each individual user access, but just grant access to the role - and users
can modify them as they wish. It should also eventually be converted to use
access entries instead of the legacy system active in parallel.

[iam role]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
````

````{tab-item} Google Cloud
:sync: gcp-key
Test deployer access by running:

```bash
deployer use-cluster-credentials $CLUSTER_NAME
```

and running:

```bash
kubectl get node
```

It should show you the provisioned node on the cluster if everything works out ok.
````

````{tab-item} Azure
:sync: azure-key
Test deployer access by running:

```bash
deployer use-cluster-credentials $CLUSTER_NAME
```

and running:

```bash
kubectl get node
```

It should show you the provisioned node on the cluster if everything works out ok.
````

````{tab-item} Jetstream2
:sync: jetstream2-key
Test deployer access by running:

```bash
deployer use-cluster-credentials $CLUSTER_NAME
```

and running:

```bash
kubectl get node
```

It should show you the provisioned node on the cluster if everything works out ok.
````
`````
