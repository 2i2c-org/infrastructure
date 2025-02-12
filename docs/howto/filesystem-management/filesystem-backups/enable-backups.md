(howto:filesystem-backups:enable)=
# Enable Automatic Filesystem Backups

This document covers how to enable automatic filesystem backups across the cloud
providers we use.

```bash
export CLUSTER_NAME=<cluster-name>
```

(howto:filesystem-backups:enable:aws)=
## AWS

```{attention}
For AWS hubs running `jupyterhub-home-nfs` only
```

To enable backups of home directories running on AWS EBS volumes, add the following line to the cluster's terraform values file.

```
enable_nfs_backup = true
```

Ensure you are in the correct terraform workspace to apply the changes:

```bash
terraform workspace select $CLUSTER_NAME
```

Then apply the changes with:

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

(howto:filesystem-backups:enable:gcp)=
## GCP

### Backup Filestores

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
        filestoreName: <filestore-name>
        project: <gcp-project>
        zone: <gcp-zone>
        serviceAccount:
          name: gcp-filestore-backups-sa
          annotations:
            iam.gke.io/gcp-service-account: <gcp-service-account-email>
      ```
      where:
      - `filestoreName` is the name of the filestore to be backed up (can be
        found from the Filestore Instances page in the GCP console)
      - `project` is the name of the GCP project in which the filestore exists
      - `zone` is the GCP zone the filestore is deployed to and where the backups
        will be stored (e.g. `us-central-b`)
      - `annotations` is the output from the `terraform apply` command in the
        previous step. You can run `terraform output gcp_filestore_backups_k8s_sa_annotations`
        to retrieve this.
2. **Upgrade the support chart.**
   ```bash
   deployer deploy-support $CLUSTER_NAME
   ```

This will have successfully enabled automatic backups of GCP Filestores for this
cluster.

#### Verify successful backups of GCP Filestores

We manually verify that backups are being successfully created and cleaned up on a regular schedule.

To verify that a backup has been recently created, and that no backups older than the retention period exist, we can use the following deployer command:

```bash
deployer verify-backups gcp <project-name> <region> <filestore-name>
```

where:
- `<project-name>` is the name of the GCP project the Filestore is located in
- `<region>` is the GCP region the Filestore is located in, e.g., `us-central1`
- `<filestore-name>` is the name of the Filestore instance

### Backup persistent disks

Backups of persistent disks are automatically enabled when defining a disk in `.tfvars` file, such as:

```
persistent_disks = {
  "staging" = {
    size        = 1
    name_suffix = "staging"
  }
}
```

Backups must be explicitly _disabled_ by adding `disable_nfs_backups = true`, like so:

```
persistent_disks = {
  "staging" = {
    size                = 1
    name_suffix         = "staging"
    disable_nfs_backups = true
  }
}
```

By default, snapshots of the disk will be scheduled to be taken at `00:00 UTC` every day, and a maximum of 5 snapshots will be retained.

```{warning}
It is not currently possible to define a backup cadence other than daily
```
