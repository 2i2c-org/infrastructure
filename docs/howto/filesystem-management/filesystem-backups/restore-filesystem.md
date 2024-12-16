(howto:filesystem-backup:restore)=
# Restore a Filesystem from a Backup

In the event of a disaster and the filesystem needs recovering, this document
covers those steps for the cloud providers.

(howto:filesystem-backup:restore:aws)=
## AWS

### Restoring home directories from an EFS recovery point

```{note}
We follow AWS's guidance for [restoring EFS from a recovery point](https://docs.aws.amazon.com/aws-backup/latest/devguide/restoring-efs.html#efs-restore-console)
```

Due to the length of the steps listed in that document, we will not repeat them here.

### Restoring home directories from EBS snapshots

On AWS, the EBS volumes used for home directories are backed up using [Data Lifecycle Manager (DLM)](https://docs.aws.amazon.com/ebs/latest/userguide/snapshot-lifecycle.html). This means that we can restore home directories from a snapshot if they are deleted or corrupted.

To restore a home directory from a snapshot, we need to create a new EBS volume from the snapshot, mount it to the EC2 instance attached to the existing EBS volume containing the NFS home directories, and then copy the contents from the restored EBS volume to the NFS home directories volume.

```{note}
Please follow AWS's guidance for [restoring EBS volumes from a snapshot](https://docs.aws.amazon.com/prescriptive-guidance/latest/backup-recovery/restore.html#restore-files) to create a new EBS volume from the snapshot.
```

Once we have created a new EBS volume from the snapshot, we need to mount it to the EC2 instance attached to the existing EBS volume containing the NFS home directories. To do this, we need to find the instance ID of the EC2 instance attached to the existing EBS volume. This involves the following steps:

1. Go to the EBS volumes page in the AWS console
2. Find the volume ID of the existing EBS volume containing the NFS home directories
3. Click on the volume ID and find the instance ID in the "Attached resources" section
4. Once we have the instance ID, we can mount the new EBS volume to the EC2 instance by following the steps outlined in the [Attaching an Amazon EBS volume to an instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-attaching-volume.html) guide.

Once we have mounted the new EBS volume to the EC2 instance, we can copy the contents from the restored EBS volume to the NFS home directories volume. This can be done by running the following commands on the EC2 instance:

```bash
# Copy the contents from the restored EBS volume to the NFS home directories volume
rsync -av --info=progress2 </restored-volume/path-to-home-directories/> </existing-volume/path-to-home-directories/>
```

Once we have copied the contents from the restored EBS volume to the NFS home directories volume, we can delete the EBS volume that was created from the snapshot.

After the restoration is complete, we should run `terraform plan` to double check that no unintended changes were made to the Terraform state.

(howto:filesystem-backup:restore:gcp)=
## GCP

```{note}
We follow GCP's guidance for [restoring fileshares from a backup](https://cloud.google.com/filestore/docs/backup-restore#restore).
```

To restore a share on a Filestore instance on GCP, we start by following the
documentation linked above. In short, this involves:

1. [Go to the Filestore instances page](https://console.cloud.google.com/filestore/instances) in the GCP console
2. Click the instance ID of the Filestore you want to restore and click the "Backups" tab
3. Locate the backup you want to restore from (most likely the most recently created), and click (...) "More actions"
4. Click "Restore backup" and then select "Source instance"
5. Click "Restore" and complete the dialog box that appears

This should successfully restore the Filestore instance to its last backed-up state.

Once this is done, you should also set the terraform variable `source_backup` to
reference this web console change. Practically, you should configure something
like below in the `terraform/gcp/projects/$CLUSTER_NAME.tfvars` file:

```
filestores = {
  "filestore" : {
    # ...
    source_backup : "projects/<gcp project name>/locations/<filestore region>/backups/<backup name>",
  },
}
```

You can determine the value of `source_backup` by trying a `terraform plan`
which should present the value in an associated error.
