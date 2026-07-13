# Regenerate credentials for NASA SMDE accounts

This document describes how we regenerate credentials for _users_ and the `deployer` when they expire in NASA SMDC accounts.

(nasa-smce:regenerate-deployer-creds)=
## Regenerate credentials for the `deployer`

1. Set the cluster name as an environment variable

   ```bash
   export CLUSTER_NAME=...
   ```

1. Authenticate yourself with https://aws.sciencecloud.nasa.gov/

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
