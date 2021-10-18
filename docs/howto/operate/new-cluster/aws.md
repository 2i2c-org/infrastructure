(new-cluster:aws)=
# Add a new AWS cluster

We do not currently use Terraform to deploy a new cluster in AWS.
Instead, we use a tool [called `kops`](https://github.com/kubernetes/kops) to provision the cluster.

:::{admonition} We also use `eksctl`
In addition to `kops`, we have begun using an AWS-native tool called `eksctl` to provision Kubernetes clusters on AWS.
See [this configuration](https://github.com/2i2c-org/infrastructure/tree/master/eksctl) for an example of a hub that uses this.
As we understand these practices better we will update this guide with more information about `eksctl`.
:::

These instructions describe how to create a new AWS cluster from scratch with `kops`.


## Pre-requisites

1. Follow the instructions outlined in [Set up and use the the deployment scripts locally](operate:manual-deploy) to set up the local environment and prepare `sops` to encrypt and decrypt files.

2. Install the awscli tool (you can use pip or conda to install it in the environment) and configure it to use the provided AWS user credentials.
   [Follow this guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-config) for a quick configuration process.

   ```{note}
   The customer with AWS admin privileges should have created a user for you with full privileges.
   We will probably explore fine-graining the permissions actually needed
   in the short-term.
   ```

3. Export some helpful AWS environment variables (because `aws configure` doesn't export these environments vars for kops to use, so we do it manually).

   ```bash
   export AWS_PROFILE=<cluster_name>
   export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
   export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
   ```

## Create a state bucket for `kops`

1. From the root directory on `infrastructure/`, `cd` into the `kops` directory
2. Set up a *state* bucket for kops. This bucket will store the cluster [state](https://kops.sigs.k8s.io/state/).

   ```bash
   export KOPS_STATE_STORE=s3://2i2c-<cluster-name>-kops-state
   aws s3 mb $KOPS_STATE_STORE --region <region>
   aws s3api put-bucket-versioning --bucket $KOPS_STATE_STORE --versioning-configuration    Status=Enabled
   ```

   ```{note}
   Kops [recommends versioning the S3 bucket]   (https://kops.sigs.k8s.io/getting_started/aws/#cluster-state-storage) in case you ever need to revert or recover a previous state store.
   ```

## Create and render a kops config file

You can use one of the existing [jsonnet](https://jsonnet.org/) specifications as a "template" for your cluster (for example, [here is the Farallon Institute specification](https://github.com/2i2c-org/infrastructure/blob/master/kops/farallon.jsonnet)).
You may need to tweak zones, names and instances, the rest is boilerplate to create a
kops-based cluster accordingly to some specification already outlined in [#28](https://github.com/2i2c-org/pangeo-hubs/issues/28).
Once you have your jsonnet specification ready, you need to render it to create the config file kops understand.

1. Render the `kops` config file with

   ```bash
   jsonnet <cluster_name>.jsonnet -y > <cluster_name>.kops.yaml
   ```

2. Regrettably, the rendering creates yaml file with with 3 dots at the end, you can  delete it with

   ```bash
   sed -i '' -e '$ d' <cluster_name>.kops.yaml
   ```

   ```{note}
   In Linux you will need to use instead: `sed -i '$ d' <cluster_name>.kops.yaml`
   ```

## Create the cluster

1. Create the cluster configuration and push it to s3 with

   ```bash
   kops create -f <cluster_name>.kops.yaml
   ```

2. You will need to a ssh key pair before actually creating the cluster

   ```bash
   ssh-keygen -f <cluster-name>.key
   ```

3. Build the cluster with the following command (notice that you are passing the ssh public key you just created in the previous step)

   ```bash
   kops update cluster <cluster_name>hub.k8s.local --yes --ssh-public-key    <cluster_name>.key.pub --admin
   ```

   ```{note}
   The `--admin` at the end will modify your `~/.kube/config` file to point to the new cluster.
   ```

   If everything went as expected, the cluster will be created after some minutes.

   ```{note}
   If you try to validate the cluster, validation will not pass until this next section is    done.
   ```

4. Relocate and encrypt the generated keys

   After creating the cluster, you will need to relocate the public and private keys with

   ```bash
   mv <cluster_name>.key ssh-keys/<cluster_name>.key
   ```

   and encrypt the private key with

   ```bash
   sops -i -e ssh-keys/<cluster_name>.key
   ```

   before pushing your changes to the repository.

   ```{note}
   You can always regenerate the public key with `ssh-keygen -y -f <cluster-name>.key`
   ```

## Apply workaround to run CoreDNS on the master node

```{seealso}
More details [in this issue](https://github.com/kubernetes/kops/issues/11199)
```

1. Patch CoreDNS with the following two commands

   ```bash
   kubectl -n kube-system patch deployment kube-dns --type json --patch '[{"op": "add", "path": "/spec/template/spec/tolerations", "value": [{"key": "node-role.kubernetes.io/master", "effect": "NoSchedule"}]}]'
   deployment.apps/kube-dns patched

   kubectl -n kube-system patch deployment kube-dns-autoscaler --type json --patch '[{"op": "add", "path": "/spec/template/spec/tolerations", "value": [{"key": "node-role.kubernetes.io/master", "effect": "NoSchedule"}]}]'
   ```

2. After applying those patches, you should be able to validate the cluster with

   ```bash
   kops validate cluster --wait 10m
   ```

## Create an EFS for your cluster

1. Install `boto3` with pip or conda

2. Create an [EFS](https://aws.amazon.com/efs/) file system for this hub with

   ```bash
   python3 setup-efs.py <cluster_name>hub.k8s.local <region-of-cluster>
   ```

This will output an fs-<xxxxxxxx> id. You should use that value
(it should be something like `fs-<id>.efs.<region>.amazonaws.com`) in
the `basehub.nfs.pv.serverIP` at you hub config file.
