(ci-cd:aws)=
# Set up CI/CD in an AWS cluster

The pilot-hubs deployer code supports [a new `auth_aws` function](https://github.com/2i2c-org/pilot-hubs/blob/e96e7bcded187870dc2e07d6626de8a12586ed32/deployer/hub.py#L126)
that can export a temporary kubeconfig file allowing a successful connection with the
kubernetes cluster.
The function expects a 2i2c generated IAM entity (a `deployer` user) and its AWS
credentials (provided as a sops encrypted `json` file). These will be used to properly
set up the AWS `Access Key ID` and `Secret Access Key` environment variables and to
allow performing operations in the cluster as the `deployer` user.

There are some pre-requisites for being able to successfully and automatically deploy hubs on AWS clusters using the provided functionality.
Follow the sections below for more information.

## Identify your type of AWS cluster
  
We are currently deploying two types of AWS clusters:

- [`EKS` clusters](https://aws.amazon.com/eks/) using Amazon's managed Kubernetes service (Carbonplan)
- [`kops` clusters](https://kops.sigs.k8s.io/getting_started/aws/) where we configure Kubernetes ourselves (Farallon,
Openscapes) clusters.

Whether to create one or another depends on the cluster operational needs and some other factors discussed in [this infrastructure issue](https://github.com/2i2c-org/pilot-hubs/issues/431).
You need to know and understand which sort of cluster are you working with to properly
set up the config file below.

:::{note}
- For instructions in setting up a `kops`-based cluster, see [the AWS cluster setup instructions](new-cluster:aws)
- Documentation about creating an `EKS`-based cluster has not yet been written
:::

## Create a `deployer` user

You will need to [create a new IAM entity](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users.html) with enough permissions to retrieve the Kubernetes context.
To do so, follow the steps below:

:::{note}
We currently set up the `deployer` user with `AdministratorAccess`, we may
want to restrict the permissions scope in the future to reduce the risk surface.
:::

- Create a new user

  ```bash
  aws iam create-user --user-name deployer
  ```

- Add the user to the `2i2c group` (assuming that group exists and has enough permissions to operate the cluster)

  ```bash
  aws iam add-user-to-group --group-name 2i2c --user-name deployer
  ```

- Check if the user was added to the group

  ```bash
  aws iam get-group --group-name 2i2c
  ```

  :::{note}
  It might be the case you do not have an existing `2i2c group`, that is not a problem   as long as you have enough permissions at the user level.
  :::

- Check permissions associated with that group/user

  ```bash
  aws iam list-attached-group-policies --group-name 2i2c
  
  aws iam list-attached-user-policies --user-name deployer
  ```

**If you are working with an `EKS`-based cluster**, you need to perform these additional steps:

- Add the user to the EKS cluster

  ```bash
  eksctl create iamidentitymapping --cluster <NAME_OF_THE_CLUSTER> --region=<REGION> --arn arn:aws:iam::<ACCOUNT_ID>:user/deployer --group system:masters --username admin
  ```

- Check if the user was added to the map

  ```bash
  eksctl get iamidentitymapping --cluster <NAME_OF_THE_CLUSTER> --region=<REGION>
  ```

## Generate credentials for the `deployer` user and encrypt them

- Get the `deployer`credentials with

  ```bash
  aws iam create-access-key --user-name deployer | tee /tmp/deployer.json
  ```

- Encrypt the `deployer.json` file before commiting it to the repository (information about encrypting files is in the [sops overview](tc:secrets:sops).

## Set up the cluster config file with additional information about the cluster

This is short snippet from the Carbonplan config file (a `EKS`-based cluster)

```yaml
provider: aws
aws:
   key: secrets/carbonplan.json
   clusterType: eks
   clusterName: carbonplanhub
   region: us-west-2
```

You must provide `aws` as the provider, and under the `aws` key there are some additional keys to be filled:

`key`
: points to the encrypted sops files containing the `deployer` credentials

`clusterType`
: whether it is an `eks` or `kops`-based cluster

`clusterName`
: the name of the kubernetes cluster

`region`
: the AWS region where the cluster lives

**If using a `kops`-based cluster**, it will need some additional information containing the state of the cluster. See this short snippet from the Farallon config for example:

```yaml
provider: aws
aws:
   key: secrets/farallon.json
   clusterType: kops
   clusterName: farallonhub.k8s.local
   region: us-east-2
   stateStore: s3://2i2c-farallon-kops-state
```

Notice the additional `stateStore` key pointing to the kops state living on a specific s3 bucket.

## Check if the cluster was added to the CI deploy-hubs workflow

The [CI deploy-hubs workflow](https://github.com/2i2c-org/pilot-hubs/blob/e96e7bcded187870dc2e07d6626de8a12586ed32/.github/workflows/deploy-hubs.yaml#L31-L36) contains the list of clusters being automatically deployed by our CI/CD system.
Make sure there is an entry for new AWS cluster.

:::{note}
We are conditionally installing `kops` if the provider is `aws` even with EKS-based
cluster. Installing `kops` is easier than developing a more sophisticated CI/CD
specification to differentiate between `kops` and EKS-based clusters. It needs to be
fixed/improved in the future.
:::
