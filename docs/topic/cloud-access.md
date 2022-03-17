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
separate billing and access control.

**To access AWS SSO**, follow these steps:

1. Log-in at [2i2c.awsapps.com/start#/](https://2i2c.awsapps.com/start#/).
2. Click on an account from the displayed options.
3. This will take you to the web console for the account.

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

### Access individual AWS accounts

For AWS accounts that are managed by clients, we use an individual AWS account for each team member, and ask the client to provide us access for each person.
To do so, follow these steps for each 2i2c engineer:

1. Ask the client to create an individual [IAM User Account](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users.html) for them.
2. This should have the broadest set of permissions for the client's account.

The canonical list of AWS accounts we have access to is maintained [in this google sheet](https://docs.google.com/spreadsheets/d/1NSaAKLG2_njXxs6JlGUAhSWeHONz9QSGLVwEK790IZo/edit#gid=537065664).
