(new-cluster:aws)=
# New Kubernetes cluster on AWS

We use [eksctl](https://eksctl.io/) to provision our k8s clusters on AWS and
terraform to provision supporting infrastructure, such as storage buckets.

(new-cluster:aws-required-tools)=
## Install required tools locally

1. Install `kubectl`, `helm`, `sops`, etc.

   In [](tutorials:setup-deploy) you find instructions on how to setup `sops` to
   encrypt and decrypt files.

2. Install [`aws`](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-instructions)

   Verify install and version with `aws --version`. You should have at least
   version 2.

3. Install or upgrade [eksctl](https://eksctl.io/introduction/#installation)

   Mac users with homebrew can run `brew install eksctl`.

   Verify install and version with `eksctl version`. You typically need a very
   recent version of this CLI.

4. Install `jsonnet`

   Mac users with homebrew can run `brew install jsonnet`.

   Verify install and version with `jsonnet --version`.

## Create a new cluster

(new-cluster:aws-setup-credentials)=
### Setup credentials

Depending on wether this project is using AWS SSO or not, you can use the following
links to figure out how to authenticate to this project from your terminal.

- [For accounts setup with AWS SSO](cloud-access:aws-sso:terminal)
- [For accounts without AWS SSO](cloud-access:aws-iam:terminal)

(new-cluster:aws:generate-cluster-files)=
### Generate cluster files

We automatically generate the files required to setup a new cluster:

- A `.jsonnet` file for use with `eksctl`
- An [ssh key](https://eksctl.io/introduction/#ssh-access) for use with eksctl
- A `.tfvars` file for use with `terraform`

You can generate these with:

```bash
export CLUSTER_NAME=<cluster-name>
export CLUSTER_REGION=<cluster-region-like ca-central-1>
export HUB_TYPE=<hub-type-like-basehub>
```

```bash
deployer generate-aws-cluster --cluster-name=$CLUSTER_NAME --cluster-region=$CLUSTER_REGION --hub-type=$HUB_TYPE
```

This will generate the following files:

1. `eksctl/$CLUSTER_NAME.jsonnet` with a default cluster configuration, deployed to `us-west-2`
2. `eksctl/ssh-keys/secret/$CLUSTER_NAME.key`, a `sops` encrypted ssh private key that can be
   used to ssh into the kubernetes nodes.
3. `eksctl/ssh-keys/$CLUSTER_NAME.pub`, an ssh public key used by `eksctl` to grant access to
   the private key.
4. `terraform/aws/projects/$CLUSTER_NAME.tfvars`, a terraform variables file that will setup
   most of the non EKS infrastructure.

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

```bash
eksctl create cluster --config-file=$CLUSTER_NAME.eksctl.yaml
```

```{tip}
Make sure the run this command **inside** the `eksctl` directory, otherwise it cannot discover the `ssh-keys` subfolder.
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

(new-cluster:aws:terraform)=
## Deploy Terraform-managed infrastructure

Our AWS *terraform* code is now used to deploy supporting infrastructure for the EKS cluster, including:

- An IAM identity account for use with our CI/CD system
- Appropriately networked EFS storage to serve as an NFS server for hub home directories
- Optionally, setup a [shared database](features:shared-db:aws)
- Optionally, setup [user buckets](howto:features:cloud-access:storage-buckets)

We still store [terraform state](https://www.terraform.io/docs/language/state/index.html)
in GCP, so you also need to have `gcloud` set up and authenticated already.

1. The steps in [](new-cluster:aws:generate-cluster-files) will have created a default `.tfvars` file.

   This file can either be used as-is or edited to enable the optional features listed above.

2. Initialise terraform for use with AWS:

   ```bash
   cd terraform/aws
   terraform init
   ```

3. Create a new [terraform workspace](topic:terraform:workspaces)

   ```bash
   terraform workspace new $CLUSTER_NAME
   ```

4. Deploy the terraform-managed infrastructure

   ```bash
   terraform plan -var-file projects/$CLUSTER_NAME.tfvars
   ```

   Observe the plan carefully, and accept it.

   ```bash
   terraform apply -var-file projects/$CLUSTER_NAME.tfvars
   ```

(new-cluster:aws:terraform:cicd)=
### Export account credentials with finely scoped permissions for automatic deployment

In the previous step, we will have created an AWS IAM user with just
enough permissions for automatic deployment of hubs from CI/CD. Since these
credentials are checked-in to our git repository and made public, they should
have least amount of permissions possible.

1. First, make sure you are in the right terraform directory:

   ```bash
   cd terraform/aws
   ```

1. Fetch credentials for automatic deployment

   ```bash
   terraform output -raw continuous_deployer_creds > ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
   ```

1. Encrypt the file storing the credentials

   ```bash
   sops --output ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json --encrypt ../../config/clusters/$CLUSTER_NAME/deployer-credentials.secret.json
   ```

1. Double check to make sure that the `config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json` file is
   actually encrypted by `sops` before checking it in to the git repo. Otherwise this can be a serious security leak!

    ```bash
   cat ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json
   ```

1. Grant the freshly created IAM user access to the kubernetes cluster.

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

2. Create a minimal `cluster.yaml` file (`config/clusters/$CLUSTER_NAME/cluster.yaml`),
   and provide enough information for the deployer to find the correct credentials.

   ```yaml
   name: <your-cluster-name>
   provider: aws
   aws:
      key: enc-deployer-credentials.secret.json
      clusterType: eks
      clusterName: <your-cluster-name>
      region: <your-region>
   hubs: []
   ```

   ```{note}
   The `aws.key` file is defined _relative_ to the location of the `cluster.yaml` file.
   ```

3. Test the access by running:

   ```bash
   deployer use-cluster-credentials $CLUSTER_NAME
   ```

   and running:

   ```bash
   kubectl get node
   ```

   It should show you the provisioned node on the cluster if everything works out ok.

## Grant `eksctl` access to other users

```{note}
This section is still required even if the account is managed by SSO. Though a
user could run `deployer use-cluster-credentials $CLUSTER_NAME` to gain access
as well.
```

AWS EKS has a strange access control problem, where the IAM user who creates
the cluster has [full access without any visible settings
changes](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html),
and nobody else does. You need to explicitly grant access to other users. Find
the usernames of the 2i2c engineers on this particular AWS account, and run the
following command to give them access:

```{note}
You can modify the command output by running `terraform output -raw eksctl_iam_command` as described in [](new-cluster:aws:terraform:cicd).
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
can modify them as they wish.

[iam role]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html

## Export the EFS IP address for home directories

The terraform run in the previous step will have also created an
[EFS instance](https://aws.amazon.com/efs/) to store the hub home directories,
and sets up the network correctly to mount it.

Get the address a hub on this cluster should use for connecting to NFS with
`terraform output nfs_server_dns`, and set it in the hub's config under
`nfs.pv.serverIP` (nested under `basehub` when necessary) in the appropriate
`<hub>.values.yaml` file.

## Add the cluster to be automatically deployed

The `deploy-hubs` GitHub workflow has a job named
[`upgrade-support-and-staging`] that need to list of clusters being
automatically deployed by our CI/CD system. Add an entry for the new cluster
here.

[`upgrade-support-and-staging`]: https://github.com/2i2c-org/infrastructure/blob/18f5a4f8f39ed98c2f5c99091ae9f19a1075c988/.github/workflows/deploy-hubs.yaml#L128-L166

## A note on the support chart for AWS clusters

````{warning}
When you deploy the support chart on an AWS cluster, you **must** enable the
`cluster-autoscaler` sub-chart, otherwise the node groups will not automatically
scale. Include the following in your `support.values.yaml` file:

```yaml
cluster-autoscaler:
  enabled: true
  autoDiscovery:
    clusterName: <cluster-name>
  awsRegion: <aws-region>
```
````
