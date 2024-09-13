(howto:filesystem-backups:enable)=
# Enable Automatic Filesystem Backups

This document covers how to enable automatic filesystem backups across the cloud
providers we use.

(howto:filesystem-backups:enable:gcp)=
## GCP

```bash
export CLUSTER_NAME=<cluster-name>
```

1. **Create relevant resources via terraform.**

   Our terraform configuration supports creating the relevant resources to support
   automatic filesystem backups, including: creating a GCP IAM Service Account
   with enough permissions to manage backups, binding that Service Account to
   a Kubernetes Service Account, and outputting the relevant annotation to use
   in helm chart config to make the relevant connections.

   1. In `terraform/gcp/projects/<cluster-name>.tfvars`, add the following variable:
      ```
      enable_filestore_backups = true
      ```
   1. Ensure you are in the correct terraform workspace to apply this change:
      ```
      terraform workspace select $CLUSTER_NAME
      ```
   1. Plan and apply the changes
      ```bash
      terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
      terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
      ```

1. **Enable the `gcpFilestoreBackups` chart in the cluster's support values.**

   1. In `config/clusters/<cluster-name>/support.values.yaml`, add the following config:
      ```yaml
      gcpFilestoreBackups:
        enabled: true
        filestoreNames:
          - <filestore-name>
          - ...
        project: <gcp-project>
        zone: <gcp-zone>
        serviceAccount:
          annotations:
            iam.gke.io/gcp-service-account: <gcp-service-account-email>
      ```
      where:
      - `filestoreNames` is a list of the filestore names to be backed up (can be
        found from the Filestore Instances page in the GCP console)
      - `project` is the name of the GCP project in which the filestore exists
      - `zone` is the GCP zone the filestore is deployed to and where the backups
        will be stored (e.g. `us-central-b`)
      - `annotations` is the output from the `terraform apply` command in the
        previous step. You can run `terraform output gcp_filestore_backups_k8s_sa_annotations`
        to retrieve this.
1. **Upgrade the support chart.**
   ```bash
   deployer deploy-support $CLUSTER_NAME
   ```

This will have successfully enabled automatic backups of GCP Filestores for this
cluster.

### Verify successful backups on GCP

We manually verify that backups are being successfully created and cleaned up on a regular schedule.

To verify that a backup has been recently created, and that no backups older than the retention period exist, we can use the following deployer command:

```bash
deployer verify-backups gcp <project-name> <region> <filestore-name>
```

where:
- `<project-name>` is the name of the GCP project the Filestore is located in
- `<region>` is the GCP region the Filestore is located in, e.g., `us-central1`
- `<filestore-name>` is the name of the Filestore instance
