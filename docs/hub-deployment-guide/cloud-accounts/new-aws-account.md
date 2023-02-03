# Create a new AWS account

When we create a new AWS account[^1], we would also need to add it to our Management Account so that all 2i2c engineers can access it via SSO[^2].
More information on these terms can be found in [](cloud-access:aws).

1. Login to AWS via SSO at https://2i2c.awsapps.com/start/#, following instructions in [](cloud-access:aws-sso)
1. Access the Management Console of the [AWS Management Account](cloud-access:aws-management-account)
1. Visit the [Organizations Accounts Console](https://us-east-1.console.aws.amazon.com/organizations/v2/home/accounts) and click "Add AWS account"
   ```{tip}
   You can find this page by searching "organizations" in the search bar once you're authenticated.
   ```
1. Pick a name for the new account.
   We try to keep the word '2i2c' out
   of the project name, in case the user decides to exercise their [right to
   replicate](https://2i2c.org/right-to-replicate/) at some point.
1. Set the email address of the account owner

   ```{tip}
   We should respect two conditions when setting up this email address:
      - don’t bottleneck on an individual’s inbox
      - use an email address that doesn't already have an AWS account associated with it (reference https://github.com/2i2c-org/infrastructure/issues/1816)
   ```

   Because of the two conditions above, we cannot use the `support.2i2c.org` email address for all the AWS accounts we create (which would have been ideal).

   Instead, we  can use the following set of steps:
      1. Use [this freshdesk guide](https://support.freshdesk.com/en/support/solutions/articles/37637-adding-multiple-email-addresses-to-freshdesk)
        to create a new freshdesk alias for the support@2i2c.org email
      2. Temporarily set the AWS account owner email address to your personal email address and follow the steps below
      3. Follow [this aws guide](https://aws.amazon.com/premiumsupport/knowledge-center/change-email-address/) to change
         the address of the account to the freshdesk alias you created in step 1.

      ```{note}
      It is not possible to use the freshdesk email alias from the account creation phase, because:
         - AWS enforces the `account@domain.com` pattern on the account email address
         - The freshdesk email alias has a `account@2i2c.freshdesk.com` pattern, which AWS doesn't like

      But it is possible to later change the email to an account like `account@2i2c.freshdesk.com`,
      and this is the workaround we're using here.
      ```
1. Click "Create AWS account" and wait for the account to be created.
   A verification email should be sent to `support@2i2c.org` to verify the new account.
1. Once the new account is created and verified, visit the [AWS accounts section of the IAM Identity Center](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/organization/accounts)
1. To add the new account to our SSO:
   * Select the checkbox next to the new account and then click the "Assign users or groups" button
   * On the "Groups" tab, select the "2i2c-engineers" group. Click "Next".
   * On the "Permission Set" page, select "AdministratorAccess". Click "Next".
   * On the "Review and submit assignments" page, click "Submit".

You have successfully created a new AWS account and connected it to our SSO Management Account!
Now, [setup a new cluster](new-cluster:aws) inside it via Terraform.

## Checking quotas and requesting increases

Finally, we should check what quotas are enforced on the account and increase them as necessary[^3].

1. Visit the [Service Quotas console](https://console.aws.amazon.com/servicequotas/home) and select "AWS services" from the left-hand side menu
2. Search for the service you would like to manage the quotas for, e.g., "Amazon Elastic Kubernetes Service (Amazon EKS)"
3. Select the quota you would like to manage, e.g., "Nodes per managed node group"
4. Click the "Request quota increase" button in the "Recent quota increase requests" section of the page
5. Fill in the form that pops up and change the quota value (must be greater than the current quota value), then click "Request"

The quotas we mostly need increasing are [EC2 quotas](https://us-east-1.console.aws.amazon.com/servicequotas/home/services/ec2/quotas) in order for new nodes to spin up.
In particular, we need to increase:

- `All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests`: This is what dask instances use (as they are spot instances)
- `Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances`: This is what is used for core and notebook instances

The values of these quotas are 'Total CPUs' and hence larger nodes consume more quota.

[^1]: AWS documentation on creating new accounts in an Organization: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_create.html>
[^2]: AWS documentation on managing account access: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html>
[^3]: AWS documentation on service quotas: <https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>
