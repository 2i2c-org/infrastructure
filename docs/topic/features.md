(hub-features-summary)=
# Features available on the hubs

This document is a concise description of various features we can
optionally enable on a given JupyterHub. Explicit instructions on how to
do so should be provided in a linked how-to document.

## GPUs

GPUs are heavily used in machine learning workflows, and we support
provisioning GPUs for users on all major platforms.

See [the associated howto guide](howto:features:gpu) for more information
on enabling this.

## Cloud permissions

Users of our hubs often need to be granted specific cloud permissions
so they can use features of the cloud provider they are on, without
having to do a bunch of cloud-provider specific setup themselves. This
helps keep code cloud provider agnostic as much as possible, while also
improving the security posture of our hubs.

### GCP

(topic:features:cloud:gcp:requestor-pays)=
#### 'Requestor Pays' access to Google Cloud Storage buckets

By default, the organization *hosting* data on Google Cloud pays for both
storage and bandwidth costs of the data. However, Google Cloud also offers
a [requester pays](https://cloud.google.com/storage/docs/requester-pays)
option, where the bandwidth costs are paid for by the organization *requesting*
the data. This is very commonly used by organizations that provide big datasets
on Google Cloud storage, to sustainably share costs of maintaining the data.

When this feature is enabled, users on a hub accessing cloud buckets from
other organizations marked as 'Requester Pays' will increase our cloud bill.
Hence, this is an opt-in feature.

```{important}
This feature enables the hub users to access `Requester Pays` buckets,
**outside** of their project.

However, note that this feature **does not** control which buckets **inside**
the project will have `Requester Pays` enabled for themselves.

1. This can be **checked** from the console following these steps in the
[GCP docs](https://cloud.google.com/storage/docs/using-requester-pays#check) or
by checking the `user_buckets` configuration in the project's terraform config
file if any `requester_pays` flag is specified because it is disabled by default.

2. **Enabling or disabling** the `Requester Pays` flag on a bucket can be achieved by
setting the [`requestor_pays`](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket#requester_pays) flag to true in our terraform config
`user_buckets` variable as described in [](howto:features:storage-buckets).
```

(topic:features:cloud:scratch-buckets)=
## 'Scratch' buckets on object storage

Users often want one or more object storage buckets
to store intermediate results, share big files with other users, or
to store raw data that should be accessible to everyone within the hub.
We can create one more more buckets and provide *all* users on the hub
*equal* access to these buckets, allowing users to create objects in them.
A single bucket can also be designated as as *scratch bucket*, which will
set a `SCRATCH_BUCKET` (and a deprecated `PANGEO_SCRATCH`) environment variable
of the form `<s3 or gcs>://<bucket-name>/<user-name>`. This can be used by individual
users to store objects temporarily for their own use, although there is nothing
preventing other users from accessing these objects!

## 'Persistent' buckets on object storage

This is exactly the same as scratch bucket storage, but *without* a rule deleting
contents after a set number of days. This is helpful for storing intermediate computational
results that take a while to compute, and are consistently used throughout the lifetime
of a project. We set the environment variable `PERSISTENT_BUCKET` to the form
`<s3 or gcs>://<bucket-name>/<user-name>` so users can put stuff in this.

```{warning}
Objects put in `PERSISTENT_BUCKET` *must* be deleted by the users when no longer in use
to prevent cost overruns! This *can not* be managed by 2i2c.
```
