(new-cluster:aws)=
# Add a new AWS cluster

We use [eksctl](https://eksctl.io/) to provision our k8s clusters on AWS.

:::{note}

We used to use [kops](https://kops.sigs.k8s.io/) as well, for clusters
where we wanted to minimize base running cost. We have deprecated that now, and use
eksctl for everything.
:::


## Install needed tools locally

1. Follow the instructions outlined in [Set up and use the the deployment
   scripts locally](operate:manual-deploy) to set up the local environment and
   prepare `sops` to encrypt and decrypt files.

2. Install the awscli tool (you can use pip or conda to install it in the
   environment) and configure it to use the provided AWS user credentials.  [Follow
   this guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-config)
   for a quick configuration process.

3. Install the latest version of [eksctl](https://eksctl.io/introduction/#installation). Mac users
   can get it from homebrew with `brew install eksctl`.

4. Put your AWS credentials (access key id and secret) in `~/.aws/credentials` file, in the following
   format:

   ```ini
   [your-cluster-name]
   aws_access_key_id = <key-id>
   aws_access_secret_key = <access-key>
   ```

   When you want to use these credentials, you can simply run `export AWS_PROFILE=<your-cluster-name>`.
   This helps manage multiple sets of credentials easily. You can validate this works by running
   `aws sts get-caller-identity`.

   ```{note}
   The customer with AWS admin privileges should have created a user for you with full privileges.
   ```

## Create an ssh key

eksctl requires an [ssh key](https://eksctl.io/introduction/#ssh-access) during
cluster creation. This is used to log in to the nodes to debug them later if necessary.
We keep the private key encrypted in `eksctl/ssh-keys`.

Generate the key with `ssh-keygen -f eksctl/ssh-keys/<cluster-name>.key`, and encrypt
the private key part with `sops --in-place --encrypt eksctl/ssh-keys/<cluster-name>.key`.
This will leave the public key unencrypted in `eksctl/ssh-keys/<cluster-name>.key.pub` -
we will use this in our eksctl config.

## Create and render an eksctl config file

We use an eksctl [config file](https://eksctl.io/usage/schema/) in YAML to specify
how our cluster should be built. Since it can get repetitive, we use
[jsonnet](https://jsonnet.org) to declaratively specify this config. You can
find the `.jsonnet` files for the current clusters in the `eksctl/` directory.

Create a new `.jsonnet` file by copying an existing one and making whatever
modifications you would like. The eksctl docs have a [reference](https://eksctl.io/usage/schema/)
for all the possible options. You'd want to make sure to change at least the following:

- Region / Zone - make sure you are creating your cluster in the correct region!
- Size of nodes in instancegroups, for both notebook nodes and dask nodes. In particular,
  make sure you have enough quota to launch these instances in your selected regions.
- Kubernetes version - older `.jsonnet` files might be on older versions, but you should
  pick a newer version when you create a new cluster.
- The ssh key path points to the `<cluster-name>.key.pub` file we created in the previous
  step

Once you have a `.jsonnet` file, you can render it into a config file that eksctl
can read.

```bash
jsonnet <your-cluster>.jsonnet > <your-cluster>.eksctl.yaml
```

## Create the cluster

Now you're ready to create the cluster!

```bash
eksctl create cluster  --config-file <your-cluster>.eksctl.yaml
```

This might take a few minutes.

If any errors are reported in the config (there is a schema validation step),
fix it in the `.jsonnet` file, re-render the config, and try again.

Once it is done, you can test access to the new cluster with `kubectl`, after
getting credentials via:

```bash
aws eks update-kubeconfig --name=<your-cluster-name> --region=<your-cluster-region>
```

`kubectl` should be able to find your cluster now! `kubectl get node` should show
you at least one core node running.

## Grant access to other users

AWS EKS has a strange access control problem, where the IAM user who creates
the cluster has [full access without any visible settings
changes](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html),
and nobody else does. You need to explicitly grant access to other users. Find
the usernames of the 2i2c engineers on this particular AWS account, and run the
following command to give them access:

```bash
eksctl create iamidentitymapping \
   --cluster <your-cluster-name> \
   --region <your-cluster-region> \
   --arn arn:aws:iam::<your-org-id>:user/<iam-user-name> \
   --username <iam-user-name> \
   --group system:masters
```

This gives all the users full access to the entire kubernetes cluster. They can
fetch local config with `aws eks update-kubeconfig --name=<your-cluster-name> --region=<your-cluster-region>`
after this step is done.

This should eventually be converted to use an [IAM Role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
instead, so we need not give each individual user access, but just grant access to the
role - and users can modify them as they wish.


## Create account with finely scoped permissions for automatic deployment

Our AWS *terraform* code can then be used to create an AWS IAM user with just
enough permissions for automatic deployment of hubs from CI/CD. Since these
credentials are checked-in to our git repository and made public, they should
have least amount of permissions possible.

1. Create a `.tfvars` file for this cluster under `terraform/aws/projects`.
   Currently, you only have to specify `region`.

2. Initialize terraform for use with AWS. We still store [terraform
   state](https://www.terraform.io/docs/language/state/index.html)
   in GCP, so you also need to have `gcloud` set up and authenticated already.

   ```bash
   cd terraform/aws
   terraform init
   ```

3. Create the appropriate IAM users and permissions.

   ```bash
   terraform apply -var-file projects/<your-cluster-name>.tfvars
   ```

   Observe the plan carefully, and accept it.

4. Fetch credentials we can encrypt and check-in to our repository so
   they are accessible from our automatic deployment.

   ```bash
   terraform output -raw continuous_deployer_creds > ../../secrets/<your-cluster-name>.json
   sops --in-place --encrypt ../../secrets/<your-cluster-name>.json
   ```

   Double check to make sure that the `../../secrets/<your-cluster-name>.json` file is
   actually encrypted by `sops` before checking it in to the git repo. Otherwise
   this can be a serious security leak!

5. Grant the freshly created IAM user access to the kubernetes cluster.

   ```bash
   eksctl create iamidentitymapping \
      --cluster <your-cluster-name> \
      --region <your-cluster-region> \
      --arn arn:aws:iam::<your-org-id>:user/hub-continuous-deployer \
      --username hub-continuous-deployer \
      --group system:masters
   ```

6. In your hub deployment file (`config/clusters/<your-cluster-name>.cluster.yaml`),
   provide enough information for the deployer to find the correct credentials.

   ```yaml
   provider: aws
   aws:
      key: secrets/<your-cluster-name>.json
      clusterType: eks
      clusterName: <your-cluster-name>
      region: <your-region>
   ```

## EFS for home directories

The terraform run in the previous step would have also created an
[EFS instance](https://aws.amazon.com/efs/) for use as home directories,
and sets up the network correctly to mount it.

Get the address the hub should use for connecting to NFS with
`terraform output nfs_server_dns`, and set it in the hub's config under
`nfs.pv.serverIP` (nested under `basehub` when necessary).

## Add the cluster to be automatically deployed

The [CI deploy-hubs
workflow](https://github.com/2i2c-org/infrastructure/blob/master/.github/workflows/deploy-hubs.yaml#L31-L36)
contains the list of clusters being automatically deployed by our CI/CD system.
Make sure there is an entry for new AWS cluster.
