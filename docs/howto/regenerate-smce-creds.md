# Regenerating credentials for NASA SMCE accounts

This document describes how we regenerate credentials for _users_ and the `deployer` when they expire in NASA SMCE accounts.

(nasa-smce:regenerate-deployer-creds)=
## Regenerate credentials for the `deployer`

1. Set the cluster name as an environment variable

   ```bash
   export CLUSTER_NAME=...
   ```

1. Authenticate yourself using the `deployer exec aws` command.
   See the `--help` information for more details.

1. Navigate to the AWS terraform folder in the infrastructure repo.

   ```bash
   cd terraform/aws
   ```

1. Initialise terraform.

   ```bash
   terraform init
   ```

1. Select the correct workspace, either by using the terraform command or setting another environment variable.

   ```bash
   # Using terraform command
   terraform workspace select $CLUSTER_NAME

   # Using an environment variable
   export TF_WORKSPACE=$CLUSTER_NAME
   ```

1. Replace the previous deployer credentials with new ones.

   ```bash
   terraform apply -replace=aws_iam_access_key.continuous_deployer -var-file=projects/$CLUSTER_NAME.tfvars
   ```

1. Export the new credentials to a file and then encrypt them in-place with `sops`.

   ```bash
   terraform output -raw continuous_deployer_creds > ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json
   sops -i -e ../../config/clusters/$CLUSTER_NAME/enc-deployer-credentials.secret.json
   ```

1. `git add` the modified files and then commit them.

   ```bash
   git commit -m "nasa smce clusters: re-generate deployer credentials"
   ```

   You can then open a Pull Request and merge it.

(nasa-smce:regenerate-user-password)=
## Regenerate a password for a user in a NASA SMCE account

The AWS accounts associated with NASA's [Science Managed Cloud Environment](https://smce.nasa.gov)
have a 60 day password expiry policy. If someone on the team misses this
deadline, we can actually reset passwords for each other!

1. Someone in the team with access logs into the AWS console of the appropriate project
2. Follow [AWS's user guide on resetting passwords](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_admin-change-user.html#id_credentials_passwords_admin-change-user_console)
   for whoever's 60 day window has elpased
3. In addition, a `AccountDisabled` IAM Group will be automatically added to the
   user whenever their credentials expire, and this will show up as a "cannot
   change password" error when the user logs in next. So the user should also be
   removed from this group. You can do so from under the "Groups" tab in the
   AWS console when looking at the details of this user.
