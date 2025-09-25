# AWS with NASA SMCE

Cloud resources for NASA's [Science Managed Cloud Environment](https://smce.nasa.gov/) (SMCE) is managed via an AWS organization and access via a SSO service.

## Signing into the AWS SSO

To sign into the AWS SSO, you need to go to the [SMCE portal](https://aws.sciencecloud.nasa.gov/). Your Science Cloud identity is tied to your 2i2c.org email address and managed via Microsoft online. Here are the steps to follow:

1. Visit the following link: [http://aws.sciencecloud.nasa.gov/](http://aws.sciencecloud.nasa.gov/)
1. Login using your 2i2c.org email address
1. Follow any instructions provided by the login process

Once logged in, you should be at the AWS Access Portal page. You should see a list of Science Cloud AWS accounts you have access to.

Clicking an account in the AWS Access Portal page shows the permissions you can use to access that account (e.g. Project-Admin or Project-Power-User or Project-Read-Only).

Select the permission level you need to perform your work, and you will be directed into the AWS console with the permissions you chose.

You can also copy and paste the access keys you require into your terminal to use the AWS CLI.

## Getting an account

This is very much the same as getting access to any other AWS account where billing is handled for us by someone else.

1. The community representative will get in touch with SMCE to either provision a new
   AWS account, or grant us full access to one that already exists.

2. Once the community representative has access, they will create an
   IAM account for *one* 2i2c engineer in this account, and make sure
   they are a part of the `SMCE-ProjectAdmins` group.  This gives us
   full access to the AWS account, and we can add other engineers here.

3. This engineer should log in with the credentials provided by the community representative, and set up [Multi Factor Authentication](https://aws.amazon.com/iam/features/mfa/), using [this dashboard link](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-west-2#/security_credentials/mfa). This is required in all SMCE environments. You need to log out of the AWS console and back in after setting up MFA to see your full permissions.

4. This engineer should now create user accounts for all other 2i2c engineers, and make sure they are all part of the `SMCE-ProjectAdmins` group.

Once this is done, steps for the regular [AWS Cluster Setup](new-cluster:new-cluster) can proceed,
until completion of [provisioning credentials for CI/CD](new-cluster:terraform:cluster-credentials).

## `hub-continuous-deployer` user

By default, we don't have permissions to create additional IAM users. This is a problem for our continuous deployer user `hub-continuous-deployer`. SMCE / SMDC is able to grant us exemptions though.

### SMDE

Right now, SMDE has to manually create the account named `hub-continuous-deployer`. This
has to be requested through their internal systems (that are opaque to us). Once created,
we can import that into our terraform with `terraform import -var-file=projects/${project}.tfvars aws_iam_user.continuous_deployer hub-continuous-deployer`.

The rest of the process should be the same.

### SMCE

The process for SMCE is a bit different. We can create the user account, but there's a
MFA requirement that must be exempted.

At the completion of [provisioning credentials for CI/CD](new-cluster:terraform:cluster-credentials),
we will have a IAM user named `hub-continuous-deployer` provisioned. This is what we use to
deploy from GitHub actions, but also to deploy from our local machines. The MFA requirement
needs to be exempted for this user before we can continue and actually deploy our hubs.

The engineer needs to reach out to the community representative at this point, and ask
for the MFA exemption. `hub-continuous-deployer` has a very narrow scope of permissions - only
`eks:DescribeCluster` on the specific cluster we deployed. The community representative will
have to reach out via their own internal processes to grant this exemption. This has
always been granted so far - VEDA, GHG - and should not be a problem to get granted again.
We have also received assurances that this process would be expedited to the extent possible.

You can verify that this MFA exemption has been processed by looking at the list of groups
the `hub-continuous-deployer` user belongs to. It should *not* contain the user `SMCE-UserRestrictions`.

Once this exemption has been processed, you can continue as usual with deployment of the hub.

## Preparing for routine regeneration of the `hub-continuous-deployer` access credentials

The `hub-continuous-deployer` has an access key and secret associated with it, this is how it
authenticates with AWS to perform actions. SMCE accounts have a 60 day password/access key
regeneration policy and so we need to prepare to regularly regenerate this access key.
See [](nasa-smce:regenerate-deployer-creds) for how to reset the credentials.

```{warning}
We only receive **5 days notice** that a password/access key will expire via email!

Also it is unclear who receives this email: all engineers or just the engineer who
setup the cluster?
```

```{note}
See [](nasa-smce:regenerate-user-password) for how to reset an expired password for
a _user_, e.g., a member of the engineering team.
```

## Cost allocation tags

[Cost allocation tags](/howto/budgeting-billing/cost-monitoring/aws.md#activate-cost-allocation-tags) have been enabled at the AWS organization level for SMCE. Therefore we do not need to enable them with our terraform configuration, i.e. the variable `enable_cost_allocation_tags` is set to `false` by default, so we do not need to include this in the `projects/<project>.tfvars` file.