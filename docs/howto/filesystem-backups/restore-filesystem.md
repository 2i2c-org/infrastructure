(howto:filesystem-backup:restore)=
# Restore a Filesystem from a Backup

In the event of a disaster and the filesystem needs recovering, this document
covers those steps for the cloud providers.

(howto:filesystem-backup:restore:gcp)=
## GCP

```{note}
We follow GCP's guidance for [restoring fileshares from a backup](https://cloud.google.com/filestore/docs/backup-restore#restore)
```

To restore a share on a Filestore instance on GCP, we follow the documentation
linked above. In short, this involves:

1. [Go to the Filestore instances page](https://console.cloud.google.com/filestore/instances) in the GCP console
1. Click the instance ID of the Filestore you want to restore and click the "Backups" tab
1. Locate the backup you want to restore from (most likely the most recently created), and click (...) "More actions"
1. Click "Restore backup" and then select "Source instance"
1. Click "Restore" and complete the dialog box that appears

This should successfully restore the Filestore instance to its last backed-up state
