# Cloud project access

We manage many projects across multiple cloud providers. This
document defines our access policy, and is the canonical location
for the projects we *do* have access to.

## Access policy

Every 2i2c engineer should have equal access to every cloud project
we maintain. This prevents particular individuals from becoming
single points of failure.

In some cases, this requires paperwork for each engineer to get
access. We should try to find ways around this, but if not,
just do the paperwork.

## Google Cloud Access

On Google Cloud, we have a [2i2c organization](https://console.cloud.google.com/projectselector2/home/dashboard?organizationId=184174754493&supportedpurview=project),
that contains some projects we are fully responsible for.
Access to *all* projects in this organization can be granted by
adding the user to the group `gcp-organization-admins@2i2c.org` in the [Google Workspace Admin dashboard](https://admin.google.com/ac/users) (available only to admins of the 2i2c.org Google Workspace account).
Note that this option is only available for engineers with a `@2i2c.org`
account.

For all other projects, we will need to make a manual entry in the project's [IAM Page](https://console.cloud.google.com/iam-admin/iam) for the engineer's `@2i2c.org` account, with `Owner` permissions.

The canonical list of GCP projects we have access to is maintained [in this google sheet](https://docs.google.com/spreadsheets/d/1NSaAKLG2_njXxs6JlGUAhSWeHONz9QSGLVwEK790IZo/edit#gid=846555027)

(cloud-access:aws)=
## AWS Access

We have two ways to access AWS accounts.

### AWS Accounts Structure

There are three units of organization in AWS that are relevant to 2i2c.

AWS Accounts
: Collections of services and infrastructure that generated their own bills. Kind-of like `projects` in Google Cloud Platform. For example, the Kubernetes cluster we run for `uwhackweeks` runs in an Account dedicated for this.

AWS Organizations
: Organizations are basically collections of accounts. They make it easy to group **access** to multiple accounts via things like [AWS Single Sign On](cloud-access:aws-sso). Every AWS Organization has a "Management Account" that defines all of the other accounts in the organization.

AWS Management Account
: A special account that is a centralized place for configuration for an AWS Organization and other accounts that might be in it. Our AWS Management account is `2i2c-sandbox`. It defines our **payment methods** for centralized payment across all of our accounts. So each of our AWS Accounts generates a bill, and these are consolidated into `2i2c-sandbox` and payed with a single credit card.

(cloud-access:aws-sso)=
### Access with Single Sign-On (SSO)

For accounts we fully control, we use [AWS SSO](https://aws.amazon.com/single-sign-on/)
to access them.
We have an [AWS organization](https://aws.amazon.com/organizations/) set up, and sub-accounts for each AWS account.
This lets us use just *one* set of user credentials for multiple AWS accounts, with
separate billing and access control. AWS maintains a [FAQ](https://aws.amazon.com/single-sign-on/faqs/)
answering many questions you may have about authentication with AWS SSO.

#### Access AWS Web console

The AWS web console is helpful to dig through various services we use, look for
error messages and other notifications, interact with support, as well as take
quick actions during an emergency situation (like an outage). You can access it by:

1. Log-in at [2i2c.awsapps.com/start#/](https://2i2c.awsapps.com/start#/).
2. Select an account from the list of displayed options.
3. Select **Management Console** to visit the AWS web console for this project.

```{note}
You can only be logged into one AWS account at a time! This can be frustrating,
as you might be working with multiple AWS accounts at the same time. In that case,
check out [Firefox Multi-Account Containers](https://addons.mozilla.org/en-US/firefox/addon/multi-account-containers/)!
```

(cloud-access:aws-sso:terminal)=
#### Access AWS from your terminal

To use programs like `eksctl`, `kops` or `terraform`, you need to get AWS credentials that
can be accessed from the terminal on your computer. When set up with AWS SSO, the portal
easily provides access with *time limited* credentials. These are valid only for **60 minutes**,
and will need to be refreshed with new sets whenever that time is up.

1. Log-in at [2i2c.awsapps.com/start#/](https://2i2c.awsapps.com/start#/).
2. Select an account from the list of displayed options.
3. Select **Commandline or programmatic access** to open a pop-up with credentials.
4. Prefer *Option 1* of copying specific environment variables, as that makes it much
   easier to use a new set of credentials when this set expires than using *Option 2* of
   putting the credentials in a file. You can also more easily authenticate to different
   AWS accounts in different terminal tabs this way.

#### Add users to our SSO

The AWS account with id `746653422107` controlled by 2i2c is used as the
[management account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_getting-started_concepts.html).
You can manage SSO users after logging in to this account.
To do so, follow these steps:

1. [Log in to the appropriate account](https://746653422107.signin.aws.amazon.com/console).
   You *must* already have a traditional IAM account created in this AWS account with
   appropriate rights to be able to add SSO users. See [this list](https://console.aws.amazon.com/iamv2/home?region=us-east-1#/users)
   after logging in for current set of IAM users.
2. Go to the [SSO users](https://console.aws.amazon.com/singlesignon/identity/home?region=us-east-1#!/users)
   page, and create an appropriate entry for the new user.
   a. Their username should match their `2i2c.org` email address.
   b. Use their `2i2c.org` address as email address.
   c. Other than email and username, provide as little info as possible. This would be
      just first name, last name and display name.
   d. "Send an email to the user with password setup instructions".
3. Add them to the `2i2c-engineers` group. This gives them access to all the other
   AWS accounts we create.
4. Create the account! They'll receive an email with appropriate instructions.

### Create new accounts in our SSO

We often create new accounts in the 2i2c organization if we want to run community-specific infrastructure attached to that account (e.g., a dedicated Kubernetes cluster).
To create a new Account under our AWS SSO, follow these steps:

1. Do XXX @yuvipanda can you fill in these steps?
2. Double check that the **quota** for this account is large enough to withstand expected usage. If not, request a quota via AWS support.

### Access individual AWS accounts

For AWS accounts that are managed by clients, we use an individual AWS account for each team member, and ask the client to provide us access for each person.
To do so, follow these steps for each 2i2c engineer:

1. Ask the client to create an individual [IAM User Account](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users.html) for them.
2. This should have the broadest set of permissions for the client's account.

The canonical list of AWS accounts we have access to is maintained [in this google sheet](https://docs.google.com/spreadsheets/d/1NSaAKLG2_njXxs6JlGUAhSWeHONz9QSGLVwEK790IZo/edit#gid=537065664).

#### Access AWS web console

1. Go to [console.aws.amazon.com/](https://console.aws.amazon.com/).
2. If asked for the kind of user you are trying to log in as, select *IAM user*.
3. Enter the 12 digit numerical account id (or account nickname, if the account has
   one) of the AWS account, your username and password.

```{note}
You can only be logged into one AWS account at a time! This can be frustrating,
as you might be working with multiple AWS accounts at the same time. In that case,
check out [Firefox Multi-Account Containers](https://addons.mozilla.org/en-US/firefox/addon/multi-account-containers/)!
```

(cloud-access:aws-iam:terminal)=
#### Access AWS from your terminal

[AWS Access Keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
are used to provide access to the AWS account from your terminal.

1. Login to the AWS web console as directed above.
2. [Create a new Access Key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey)
   for your user account.
3. Put your newly generated AWS credentials (access key id and secret) in `~/.aws/credentials` file, in the following
   format:

   ```ini
   [your-cluster-name]
   aws_access_key_id = <key-id>
   aws_access_secret_key = <access-key>
   ```

   When you want to use these credentials, you can simply run `export AWS_PROFILE=<your-cluster-name>`.
   This helps manage multiple sets of credentials easily. You can validate this works by running
   `aws sts get-caller-identity`.