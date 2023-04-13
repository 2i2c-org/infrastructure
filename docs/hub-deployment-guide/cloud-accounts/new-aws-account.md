# Create a new AWS account

When we create a new AWS account[^1], we create it to be a AWS Member Account to
our AWS Management Account `2i2c-sandbox`. We then grant permissions to a group
of IAM users in the management account to manage the created member account.
Like this, we can sign in to manage the member accounts using users defined in
the `2i2c-sandbox` account.

More information on these terms can be found in [](cloud-access:aws).

1. Login at https://2i2c.awsapps.com/start/#

2. Visit the Management Console of `2i2c-sandbox`, the [AWS Management Account](cloud-access:aws-management-account)

3. Visit the [Organizations Accounts Console](https://us-east-1.console.aws.amazon.com/organizations/v2/home/accounts) and click "Add an AWS account"

   ```{tip}
   You can find this page by searching "organizations" in the search bar once you're authenticated.
   ```

4. Enter an AWS account name

   Avoid using `2i2c` in the account name in case the user decides to exercise
   their [right to replicate](https://2i2c.org/right-to-replicate/) at some
   point.

5. Enter an email address for the account's owner

   Use `support+aws-<aws account name>@2i2c.org`, like `support+aws-smithsonian@2i2c.org`. It will still be delivered to `support@2i2c.org` but still function as a unique username identifier. This is called [subaddressing].

   [subaddressing]: https://en.wikipedia.org/wiki/Email_address#Subaddressing

6. Click "Create AWS account"

7. Once the new account is created, visit the [AWS accounts section of the IAM Identity Center](https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/organization/accounts)

8. To add the new account to our SSO:
   * Select the checkbox next to the new account and then click the "Assign users or groups" button
   * On the "Groups" tab, select the "2i2c-engineers" group. Click "Next".
   * On the "Permission Set" page, select "AdministratorAccess". Click "Next".
   * On the "Review and submit assignments" page, click "Submit".

You have successfully created a new AWS account and connected it to our AWS Organization's Management Account!
Now, [setup a new cluster](new-cluster:aws) inside it via Terraform.

## Checking quotas and requesting increases

Cloud providers like AWS require their users to request a _Service Quota
increase_[^2] for any substantial use of their services. Quotas act as an upper
bound of for example the number of CPUs from a certain machine type and the
amount of public IPs that the account can acquire.

When an AWS account is created under our AWS Organization, a Service Quota
increase request is automatically submitted thanks to what AWS refer to
"Organization templates", "Quota request template", and "Template
association"[^3].

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
[^2]: AWS documentation on service quotas: <https://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html>
[^3]: AWS documentation on request templates: <https://docs.aws.amazon.com/servicequotas/latest/userguide/organization-templates.html>
