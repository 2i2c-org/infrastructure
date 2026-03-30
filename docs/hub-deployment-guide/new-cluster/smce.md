# AWS with NASA SMCE

Cloud resources for NASA's [Science Managed Cloud Environment](https://smce.nasa.gov/) (SMCE) is managed via an AWS organization and access via a SSO service.

Once the steps below are done, steps for the regular [AWS Cluster Setup](new-cluster:new-cluster) can proceed,
until completion of [provisioning credentials for CI/CD](new-cluster:terraform:cluster-credentials).

## Getting an account

1. The community representative will get in touch with SMCE to setup a Science Cloud account for each 2i2c member.
2. This account will have to be added by the community to their AWS SSO.
3. We will then be able to login each of the SMCE AWS accounts we have access to.

## Signing into the AWS SSO

### Via the UI

To sign into the AWS SSO, you need to go to the [SMDC portal](https://aws.sciencecloud.nasa.gov/). Your Science Cloud identity is tied to your 2i2c.org email address and managed via Microsoft online. Here are the steps to follow:

1. Visit the following link: [http://aws.sciencecloud.nasa.gov/](http://aws.sciencecloud.nasa.gov/)
1. Login using your 2i2c.org email address
1. Follow any instructions provided by the login process

Once logged in, you should be at the AWS Access Portal page. You should see a list of Science Cloud AWS accounts you have access to.

Clicking an account in the AWS Access Portal page shows the permissions you can use to access that account (e.g. Project-Admin or Project-Power-User or Project-Read-Only).

Select the permission level you need to perform your work, and you will be directed into the AWS console with the permissions you chose.

You can also copy and paste the access keys you require into your terminal to use the AWS CLI.

### Via the terminal
Follow the instructions at [](cloud-access:aws-sso:terminal) to get access into the cluster.

The rest of the process should be the same.

## Get eksctl access into the cluster for everyone using an AWS SSO user

1. Login into the hub via the terminal following the steps linked above.
2. Assume the Project-Admin role for the cluster you want to get access to.
2. Get the exact role name assumed by the SSO user as follows:
   ```bash
   role=$(aws sts get-caller-identity --query "Arn" --output text | grep --only-matching -E "AWS[^\/]+")
   ```
3. From the role name, determine the ARN
   ```bash
   arn=$(aws iam get-role --role-name "$role" --output text --query Role.Arn)
   ```
4. Create an access entry for this ARN
   ```bash
   aws eks create-access-entry --cluster-name "$CLUSTER_NAME" --principal-arn "$arn" --region "$REGION"
   ```
5. Associate that access entry with the AmazonEKSClusterAdminPolicy
   ```bash
   aws eks associate-access-policy \
   --cluster-name "$CLUSTER_NAME" \
   --region "$REGION" \
   --principal-arn "$arn" \
   --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
   --access-scope type=cluster
   ```

## `hub-continuous-deployer` user

By default, we don't have permissions to create additional IAM users. This is a problem for our continuous deployer user `hub-continuous-deployer`. SMCE is able to grant us exemptions though.

Right now, SMDE has to manually create the account named `hub-continuous-deployer`. This
has to be requested through their internal systems (that are opaque to us). Once created,
we can import that into our terraform with `terraform import -var-file=projects/${project}.tfvars aws_iam_user.continuous_deployer hub-continuous-deployer`.

## Cost allocation tags

[Cost allocation tags](howto:cost-monitoring:activate-tags) have been enabled at the AWS organization level for SMCE. Therefore we do not need to enable them with our terraform configuration, i.e. the variable `enable_cost_allocation_tags` is set to `false` by default, so we do not need to include this in the `projects/<project>.tfvars` file.