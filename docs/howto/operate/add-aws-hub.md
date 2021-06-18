# Add a new hub in a AWS kops-based cluster

The idea behind this guide is showcase the process of setting up a 
[kops](https://kops.sigs.k8s.io/getting_started/aws/)-based AWS
cluster and manually deploy a new hub on top of it using our deployer tool.
This is a preliminary but fully functional and manual process. Once
[#381](https://github.com/2i2c-org/pilot-hubs/issues/381) is resolved, we should be able
to automate the hub deployment process as we currently do with the GKE-based hubs.

```{note}
We will continue working toward a definitive one once we figured out some of the
discussions outlined in [#431](https://github.com/2i2c-org/pilot-hubs/issues/431).
```

## Pre-requisites

1. Follow the instructions outlined in
[Set up and use the the deployment scripts locally](./manual-deploy.md) to set up the
local environment and prepare `sops` to encrypt and decrypt files.

2. Install the awscli tool (you can use pip or conda to install it in the environment)
and configure it to use the provided AWS user credentials. [Follow this guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-config)
for a quick configuration process.

```{note}
The customer with AWS admin privileges should have created a user for you with full
privileges. We will probably explore fine-graining the permissions actually needed
in the short-term.
```

3. Export some helpful AWS environment variables (because `aws configure` doesn't export
these environments vars for kops to use, so we do it manually).

```bash
export AWS_PROFILE=<cluster_name>
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
```

## Create an AWS kops-based cluster

1. From the root directory on this repo, `cd` into the `kops` directory
2. Set up a *state* bucket for kops. This bucket will store the cluster
[state](https://kops.sigs.k8s.io/state/).

``` bash
export KOPS_STATE_STORE=s3://2i2c-<cluster-name>-kops-state
aws s3 mb $KOPS_STATE_STORE --region <region>
aws s3api put-bucket-versioning --bucket $KOPS_STATE_STORE --versioning-configuration Status=Enabled
```

```{note}
Kops [recommends versioning the S3 bucket](https://kops.sigs.k8s.io/getting_started/aws/#cluster-state-storage) in case you ever need to revert or recover a previous state
store.
```

### Create and render a kops config file

You can use 
of the existing [jsonnet](https://jsonnet.org/) specifications as a "template" for your cluster (for example, [here is the Farallon Institute specification](https://github.com/2i2c-org/pilot-hubs/blob/master/kops/farallon.jsonnet)).
You may need to tweak zones, names and instances, the rest is boilerplate to create a
kops-based cluster accordingly to some specification already outlined in 
[#28](https://github.com/2i2c-org/pangeo-hubs/issues/28). Once you have your jsonnet
specification ready, you need to render it to create the config file kops understand.

1. Render the `kops` config file with

```bash
jsonnet <cluster_name>.jsonnet -y > <cluster_name>.kops.yaml
```

2. Regrettably, the rendering creates yaml file with with 3 dots at the end, you can 
delete it with

```bash
sed -i '' -e '$ d' <cluster_name>.kops.yaml
```

```{note}
In Linux you will need to use instead: `sed -i '$ d' <cluster_name>.kops.yaml`
```

### Create the cluster

1. Create the cluster configuration and push it to s3 with

```bash
kops create -f <cluster_name>.kops.yaml
```

2. You will need to a ssh key pair before actually creating the cluster

```bash
ssh-keygen -f <cluster-name>.key
```

3. Build the cluster with the following command (notice that you are passing the ssh public key you just 
created in the previous step)

```bash
kops update cluster <cluster_name>hub.k8s.local --yes --ssh-public-key <cluster_name>.key.pub --admin
```

```{note}
The `--admin` at the end will modify your `~/.kube/config` file to point to the new 
cluster.
```

If everything went as expected, the cluster will be created after some minutes.

```{note}
If you try to validate the cluster, validation will not pass until this next section is done.
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

### Apply workaround to run CoreDNS on the master node

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

### Create an EFS for your cluster

1. Install `boto3` with pip or conda

2. Create an [EFS](https://aws.amazon.com/efs/) file system for this hub with

```bash
python3 setup-efs.py <cluster_name>hub.k8s.local <region-of-cluster>
```

This will output an fs-<xxxxxxxx> id. You should use that value 
(it should be something like `fs-<id>.efs.<region>.amazonaws.com`) in
the `basehub.nfsPVC.nfs.serverIP` at you hub config file. 

## Deploy the new hub

1. First, `cd` back to the root of the repository

2. Generate a kubeconfig that will be used by the deployer with

```bash
KUBECONFIG=secrets/<cluster_name>.yaml kops export kubecfg --admin=730h <cluster_name>hub.k8s.local
```

3. Encrypt (in-place) the generated kubeconfig with sops

```bash
sops -i -e secrets/<cluster_name>.yaml
```

4. Generate a new config file for your cluster

You can use of the existing cluster config files as a "template" for your cluster (for example, [here is the Farallon Institute config file](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs/farallon.cluster.yaml)).
You may need to tweak names, `serverIP` and singleuser's images references. Make sure 
you set up the `profileList` section to be compatible with your kops cluster (ie. match 
the `node_selector` with the proper `instance-type`).

5. Set `proxy.https.enabled` to `false`. This creates the hubs without trying to give 
them HTTPS, so we can appropriately create DNS entries for them.

6. Deploy the hub (or hubs in case you are deploying more than one) without running the
test with

```bash
python3 deployer deploy <cluster_name> --skip-hub-health-test
```

7. Get the AWS external IP for your hub with (supposing your hub is `staging`):

```bash
kubectl -n staging get svc proxy-public
```

Create a CNAME record for `staging.foo.2i2c.cloud` and point it to the AWS external IP.


```{note}
Wait for about 10 minutes to make sure the DNS records actually resolves properly.
If you are deploying `prod` hub as well, you will need to repeat this step for `prod`.
```

8. Set `proxy.https.enabled` to `true` in the cluster config file so we can get HTTPS.

9. Finally run the deployer again with 

```bash
python3 deployer deploy <cluster_name>
```

This last run should setup HTTPS and finally run a test suite.
