# AWS with external account

In some cases, the organization has its own AWS account that is provided to us to deploy the cluster.
This method is far simpler as we don't have to handle cloud billing, since it is handled by the organization.

There are some steps to do before the deploy:

1. Instruct the external organization to create one AWS IAM account with full permissions.
   Since we will have one account per engineer,
   this initial account should be created for the specific engineer who is responsible for setting up the hub.

1. The organization sends the credentials for this account to `support@2i2c.org`,
   [encrypted using age encryption method](inv:dc#support:encrypt).

1. The engineer accesses this information and [decrypts it using the provided instructions](/sre-guide/support/decrypt-age).

1. This engineer can use the IAM service in the AWS Console to create accounts for each of the other engineers
   and then sends the credentials to each, for example, through Slack.
   
   ```{tip}
   Create a **User group** with admin permissions.
   ```

1. Continue with the cluster setup as usual (following [new cluster runbook](hub-deployment-guide:runbooks:phase2)).
