# Mount S3 Buckets as a filesystem

Some communities want to make object storage (like S3)
appear as if it was a classic filesystem. While it's ideal
to treat object storage as its own thing, and many libraries
(such as `xarray`) support talking directly to object storage,
many users are still much more familiar with classic filesystem
operations. Many users often end up downloading files from
object storage onto their home directories or `/tmp` before
working on them, and directly being able to access them as
a filesystem helps reduce the complexity here.

The long term solution is still to adopt tools that are
'cloud native' and can talk directly to object storage. But
in the meantime, being able to mount object storage as a
classic filesystem is helpful.

This document describes how we can provide this via
[S3Files](https://aws.amazon.com/s3/features/files/)
on AWS.

```{note}
Prior to S3Files, [FUSE](https://en.wikipedia.org/wiki/Filesystem_in_Userspace)
is how this service was provided. However, everyone who uses
FUSE eventually regrets it, so let us learn from those mistakes
and not use FUSE if we can.
```

## Who should use this?

It's tempting to just make your entire object store available
this way. Don't! There are a few considerations:

1. Medium to long term, adopting code that talks directly to
   object storage is the way to go. This is purely a stop-gap,
   available for folks who are in the process of doing this
   migration.
2. This costs additional cloud costs, in ways that can be very
   non-intuitive since it's charged both for cache storage,
   retrieval and includes a minimum cap on how much data can
   be read at a time (see [last week in AWS talking about it](https://www.lastweekinaws.com/blog/s3-is-not-a-filesystem-but-now-theres-one-in-front-of-it/)).
   The cost factors are not fully understood yet, and this could
   lead you to a surprise bill because someone ran `find .`
   on their home directory
3. Since buckets are global, if you mount buckets *read-write*,
   users can write over each other accidentally. This can
   also happen over object storage directly, but when viewed
   as a filesystem is more likely since most filesystems are
   not shared with other users.

For these and other reasons, the current recommendation is
to only mount these *readonly*, for existing datasets, in
communities where there is a lot of existing code that relies
on the filesystem.

## Enabling S3Files

1. In the terraform vars file for the cluster, add a list of
   buckets + hubs where they would be hosted.


   ```terraform
   s3files = {
    "key-name": {
      bucket : "<name-of-bucket>",
      hubs   : ["hub1", "hub2"]
    },
    "key2": {
      bucket : "<name-of-bucket>",
      hubs   : ["hub1"]
    }
   }
   ```

   This creates one S3Files Filesystem for each bucket, for each
   hub, and tags them appropriately. By creating a filesystem per
   hub for each bucket, we are able to attribute cloud costs to
   the particular hub.

   ```{note}
   Only buckets with [Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
   enabled can be used with S3 files.
   ```

   Apply the changes, and take a look at the `terraform outputs`.

   You'll need the following two values from here for the
   next steps:
   - `s3files_efs_csi_driver_role`
   - `s3files_fs_map`

2. In the `eksctl/<cluster-name>.jsonnet` file, we need to enable
   the [EFS CSI Driver](https://docs.aws.amazon.com/eks/latest/userguide/s3files-csi.html)
   and give it enough rights to mount buckets.

   ```jsonnet
    local c = cluster.makeCluster(
        ...,
        extraAddons=[
            {
                name: "aws-efs-csi-driver",
                serviceAccountRoleARN: "<arn-from-terraform-output-s3files_efs_csi_driver_role>"
            }
        ]
    )
   ```

   The `serviceAccountRoleARN` value is the value from `terraform
   output s3files_efs_csi_driver_role` from the previous step.

   After editing this, you can render the file into YAML with
   `jsonnet <cluster-name>.jsonnet > <cluster-name>.yaml`. You
   can then create the addon with `eksctl create addon --config-file <cluster-name>.yaml`.

   ```{note}
   If you're editing the addon config and updating it, you can
   re-render the jsonnet and use the `eksctl update addon --config-file <cluster-name>.yaml`
   instead of `eksctl create`.

3. Finally, we mount the buckets in the appropriate hubs. The
   terraform output `s3files_fs_map` you saved from step 1
   comes in handy here. It lists the config for each hub in
   YAML so you can just copy paste. For example, it may look
   like this:

   ```
   s3files_fs_map = {
    "staging" = <<-EOT
    "schmidt-observatory-system":
        "bucketName": "schmidt-observatory-system"
        "volumeHandle": "fs-00abd9668906bc93d"

    EOT
    "workshop" = <<-EOT
    "schmidt-observatory-system":
        "bucketName": "schmidt-observatory-system"
        "volumeHandle": "fs-0122cfff59073f460"

    EOT
   }
   ```

   It maps the bucket to the appropriate `volumeHandle`,
   splitting out the config per-hub. You can copy the config
   into the appropriate `<hub-name>.values.yaml` file, under
   `jupyterhub.custom.s3files.mounts`. A `staging.values.yaml`
   file will thus look like this:

   ```yaml
   jupyterhub:
     custom:
       s3files:
         enabled: true
         mounts:
            schmidt-observatory-system:
                bucketName: "schmidt-observatory-system"
                volumeHandle: "fs-00abd9668906bc93d"
   ```

   This will mount these buckets under `~/s3/<bucket-name>`
   for all users!

   ```{note}
   Don't forget to set `jupyterhub.s3files.enabled` to `true`
   ```
