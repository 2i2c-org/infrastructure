# Create a new AWS account

When we create a new AWS account[^1], we also add it to our Management Account
(`2i2c-sandbox`) so that all 2i2c engineers can access it via SSO[^2].

More information on these terms can be found in [](cloud-access:aws).

1. Login to AWS via SSO at https://2i2c.awsapps.com/start/#, following instructions in [](cloud-access:aws-sso)

1. Access the Management Console of the [AWS Management Account](cloud-access:aws-management-account)

1. Visit the [Organizations Accounts Console](https://us-east-1.console.aws.amazon.com/organizations/v2/home/accounts) and click "Add AWS account"

   ```{tip}
   You can find this page by searching "organizations" in the search bar once you're authenticated.
   ```

2. Pick a name for the new account.

   Avoid using `2i2c` in the account name in case the user decides to exercise
   their [right to replicate](https://2i2c.org/right-to-replicate/) at some
   point.

3. Set the email address of the account owner

   ```{tip}
   We should respect two conditions when setting up this email address:
      - don’t bottleneck on an individual’s inbox
      - use an email address that doesn't already have an AWS account associated with it (reference https://github.com/2i2c-org/infrastructure/issues/1816)
   ```

   Because of the two conditions above, we cannot use the `support@2i2c.org` email address for all the AWS accounts we create (which would have been ideal).

   Instead, we can use the following set of steps:

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

4. Click "Create AWS account" and wait for the account to be created.
   A verification email should be sent to `support@2i2c.org` to verify the new account.

5. Once the new account is created and verified, visit the [AWS accounts section of the IAM Identity Center](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/organization/accounts)

6. To add the new account to our SSO:
   * Select the checkbox next to the new account and then click the "Assign users or groups" button
   * On the "Groups" tab, select the "2i2c-engineers" group. Click "Next".
   * On the "Permission Set" page, select "AdministratorAccess". Click "Next".
   * On the "Review and submit assignments" page, click "Submit".

You have successfully created a new AWS account and connected it to our AWS Organization's Management Account!
Now, [setup a new cluster](new-cluster:new-cluster-aws) inside it via Terraform.

## Checking quotas and requesting increases

Cloud providers like AWS require their users to request a _Service Quota
increase_[^3] for any substantial use of their services. Quotas acts as an upper
bound of for example the number of CPUs from a certain machine type and the
amount of public IPs that the account can acquire.

When an AWS account is created under our AWS Organization, a Service Quota
increase request is automatically submitted thanks to what AWS refer to
"Organization templates", "Quota request template", and "Template
association"[^4].

Following account creation, make sure to check our emails to see what is being
requested and if its approved.


We typically need to increase three kinds of quotas described below. The values
of these are all 'Total CPUs' and hence larger nodes consume more quota.

- **Standard instance quota** (`Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances`)

  These instances are what we use for everything besides the exceptions noted
  below.

  All our hubs will require an increase in this quota.

- **Spot instance quota** (`All Standard (A, C, D, H, I, M, R, T, Z) Spot Instance Requests`)

  A spot instance is a cheaper instance not guaranteed to be available like
  standard instances are. We configure these to be used by dask worker pods as
  created for dask-gateway provided clusters.

  Our `daskhub` hubs will require an increase in this quota.

- **GPU instance or high memory instance quota**

  A GPU instance quota (`Running On-Demand G and VT instances`, `Running
  On-Demand P instances`) or a High Memory instance quota (`Running On-Demand
  High Memory instances`) is requested specifically to be able to use GPU
  powered machines or machines with high amounts of RAM memory.

  Our custom tailored hubs will require an increase in this quota.

### Manually requesting a quota increase

1. Visit the [Service Quotas console](https://console.aws.amazon.com/servicequotas/home) and select "AWS services" from the left-hand side menu
2. Search for the service you would like to manage the quotas for, e.g., "Amazon Elastic Kubernetes Service (Amazon EKS)"
3. Select the quota you would like to manage, e.g., "Nodes per managed node group"
4. Click the "Request quota increase" button in the "Recent quota increase requests" section of the page
5. Fill in the form that pops up and change the quota value (must be greater than the current quota value), then click "Request"

[^1]: AWS documentation on creating new accounts in an Organization: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_create.html>
[^2]: AWS documentation on managing account access: <https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html>
[^3]: AWS documentation on service quotas: <https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>
[^4]: AWS documentation on request templates: <https://docs.aws.amazon.com/servicequotas/latest/userguide/organization-templates.html>
