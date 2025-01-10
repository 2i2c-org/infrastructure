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

Once we have created a new EBS volume from the snapshot, we can use the `deployer exec root-homes` command to mount the new EBS volume to a pod along with the existing NFS home directories volume.

```bash
deployer exec root-homes $CLUSTER_NAME $HUB_NAME --additional-volume-id=<new-ebs-volume-id> --additional-volume-mount-path=/restore-volume
```

Now, the NFS home directories volume is mounted to the pod along with the new EBS volume. We can now copy the contents from the restored EBS volume to the NFS home directories volume.

If we want to do a full restore and/or we are restoring data to a new and empty NFS home directories volume, we can use the following command to copy everything from the restored EBS volume to the NFS home directories volume.

```bash
rsync -av --info=progress2 /restore-volume/ /root-homes/
```

If we want to do a partial restore and we are restoring only a subset of the data to an existing NFS home directories volume, we can use the following command to copy only the necessary data from the restored EBS volume to the NFS home directories volume.

```bash
rsync -av --info=progress2 /restore-volume/<path-to-restore> /root-homes/<path-to-restore>
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
