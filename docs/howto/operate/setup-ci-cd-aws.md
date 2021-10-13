(operate:setup-ci-cd-aws)=
# Set up the CI/CD system in an AWS cluster

The pilot-hubs deployer code supports [a new `auth_aws` function](https://github.com/2i2c-org/pilot-hubs/blob/e96e7bcded187870dc2e07d6626de8a12586ed32/deployer/hub.py#L126)
to get a temporary kubeconfig file that allows a successful connection with the
kubernetes cluster.
It is actually expecting a 2i2c generated IAM entity (the `deployer` user) and its
AWS credentials (that we provide in a sops encrypted json file) to properly set them up
as the AWS `Access Key ID` and `Secret Access Key` as environment variables and
successfully perform operations in the cluster as the `deployer` user.

There are some requisites for being able to successfully and automatically deploy hubs
on AWS clusters using the provided functionality:

1. Find out if you are working with a [AWS EKS-based](https://aws.amazon.com/eks/) or a
[kops-based](https://kops.sigs.k8s.io/getting_started/aws/) cluster
  
   We are currently deploying `EKS`-based (Carbonplan) and `kops`-based (Farallon,
   Openscapes) clusters. Whether to create one or another depends on the cluster
   operational needs and some other factors outlined and being discussed in a dedicated
   [pilot-hub issue](https://github.com/2i2c-org/pilot-hubs/issues/431).
   You need to know and understand which sort of cluster are you working with to properly
   set up the config file in step 4.

   Look at [the AWS cluster setup instructions](new-cluster:aws) if you are interested in
   setting up a `kops`-based cluster.

   :::{note}
   Documentation about creating an `EKS`-based cluster has not yet being written
   :::

2. Create a `deployer` user with enough permissions for being able to automatically
retrieve the kubernetes context.

   :::{note}
   We are currently setting up the `deployer` user with `AdministratorAccess`, we may
   want to restrict the permissions scope in the future to reduce the risk surface.
   :::

   * Create a new user

   ```bash
   aws iam create-user --user-name deployer
   ```

   * Add the user to the `2i2c group` (assuming that group exists and have enough
   permissions to operate the cluster)

   ```bash
   aws iam add-user-to-group --group-name 2i2c --user-name deployer
   ```

   * Check if the user was added to the group

   ```bash
   aws iam get-group --group-name 2i2c
   ```

   :::{note}
   It might be the case you do not have an existing `2i2c group`, that is not a problem
   as long as you have enough permissions at the user level.
   :::

   * Check permissions associated with that group/user

   ```bash
   aws iam list-attached-group-policies --group-name 2i2c

   aws iam list-attached-user-policies --user-name deployer
   ```

   If you are working with a `EKS`-based cluster, you need to perform these additional
   steps:

   * Add the user to the EKS cluster

   ```bash
   eksctl create iamidentitymapping --cluster <NAME_OF_THE_CLUSTER> --region=<REGION> --arn arn:aws:iam::<ACCOUNT_ID>:user/deployer --group system:masters --username admin
   ```

   * Check if the user was added to the map

   ```bash
   eksctl get iamidentitymapping --cluster <NAME_OF_THE_CLUSTER> --region=<REGION>
   ```

3. Generate credentials for such a user and encrypted them

   * Get the `deployer`credentials with

   ```bash
   aws iam create-access-key --user-name deployer | tee /tmp/deployer.json
   ```

   * Encrypt the `deployer.json file before commiting it to the repository.

   :::{note}
   You can find more information about encrypting files in the [sops overview](see {ref}`tc:secrets:sops`)
   :::

4. Set up the cluster config file with additional information about the cluster

   This is short snippet from the Carbonplan config file (a `EKS`-based cluster)

   ```yaml
   provider: aws
   aws:
     key: secrets/carbonplan.json
     clusterType: eks
     clusterName: carbonplanhub
     region: us-west-2
   ```

   You may notice you need to provide `aws` as the provider and then, under the `aws` key,
   there is some additional keys to be filled:

     * `key`, that one points to the encrypted sops files containing the `deployer` credentials
     * `clusterType`, whether it is an `eks` or `kops`-based cluster
     * `clusterName`, the name of the kubernetes cluster
     * `region`, the AWS region where the cluster lives

   The `kops`-based cluster need some additional information containing the state of the cluster

   This is short snippet from the Farallon config file

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

5. Check if the cluster was added to the [CI deploy-hubs workflow](https://github.com/2i2c-org/pilot-hubs/blob/e96e7bcded187870dc2e07d6626de8a12586ed32/.github/workflows/deploy-hubs.yaml#L31-L36)

   :::{note}
   We are conditionally installing `kops` if the provider is `aws` even with EKS-based cluster.
   :::


 