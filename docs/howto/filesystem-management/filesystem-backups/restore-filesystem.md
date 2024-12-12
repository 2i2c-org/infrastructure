(howto:filesystem-backup:restore)=
# Restore a Filesystem from a Backup

In the event of a disaster and the filesystem needs recovering, this document
covers those steps for the cloud providers.

(howto:filesystem-backup:restore:aws)=
## AWS

```{note}
We follow AWS's guidance for [restoring EFS from a recovery point](https://docs.aws.amazon.com/aws-backup/latest/devguide/restoring-efs.html#efs-restore-console)
```

Due to the length of the steps listed in that document, we will not repeat them here.

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
