# Apply Cloud Credits

On each cloud provider, it is common to provide cloud credits that cover the infrastructure costs instead of paying with cash.
This page has information about how this works for each major cloud provider we use.

## Amazon Web Services

On Amazon Web Services, credits come via **Promotion Codes**.
These are unique strings that are attached to a given credit offer.
We can apply these codes to any Account in AWS.
To do so, follow these steps:

1. Log in to the relevant account via [our AWS SSO](cloud-access:aws-sso).
2. Confirm that you are in the right account! Credits will *only be available for this account*, and unavailable in any other accounts in the 2i2c AWS organization.
   So *make sure you are in the correct account* before applying them.
3. Go to {guilabel}`AWS Billing` -> {guilabel}`Credits`
4. Click {guilabel}`Redeem Credit` in the top-right.
5. Enter the Promotion Code and click {guilabel}`Redeem Credit` in the bottom-right.

### Expiration dates

AWS credits come with an expiration date that is listed on the {guilabel}`Credits` page.
You must use all of the credits before this date, or they will expire.

### We don't share credits across accounts

You can share AWS credits between Accounts that are within the same organization.
This is called **Credit Sharing** for [**Consolidated Billing Accounts**](https://aws.amazon.com/premiumsupport/knowledge-center/consolidated-billing-credits/).
In this case, we have one Billing Account that pays for activity across a number of other AWS accounts in the 2i2c AWS organization.

However, **2i2c turns off credit sharing** for its accounts.
This is because credits are usually attached to a specific community, which tends to have a dedicated account.
We turn off credit sharing so that one community's credits do not get shared with a different community.

## Google Cloud

On Google Cloud, credits are attached directly to a **Billing Account**.
This is the account that pays for the cloud costs across any **Projects** that are linked to the account.

If a community has Google Cloud credits that are available to it, a Google Representative will usually need to know the Billing Account to attach credits to.
There is no way for credits to be ear-marked for a specific Project, if there are multiple projects linked to a Billing Account.
For this reason, we usually create a dedicated billing account for these credits, following the steps below:

1. Go to [the Google Cloud console](https://console.cloud.google.com/)
2. Make sure you've logged in with an account that has **Billing Administrator** permissions.
3. Create a billing account by [following the Google Cloud instructions](https://cloud.google.com/billing/docs/how-to/manage-billing-account).
4. Note the account name, and the **Billing account ID**.
5. Send this information to the Google Rep, and they'll attach the credits to the account.
6. Make sure that this account is linked to the GCP Project that will run the infrastructure for this community.
