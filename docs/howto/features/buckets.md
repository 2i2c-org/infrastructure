(howto:features:storage-buckets)=
# Setup object storage buckets

See [the relevant topic page](topic:features:cloud:scratch-buckets) for more information
on why users want this!

1. In the `.tfvars` file for the project in which this hub is based off
   create (or modify) the `user_buckets` variable. The config is
   like:

   ```terraform
   user_buckets = {
      "bucket1": {
         "delete_after": 7
      },
      "bucket2": {
         "delete_after": null
      },
      "bucket3": {
         "archival_storageclass_after": 3
      }
   }
   ```

   Since storage buckets need to be globally unique across all of Google Cloud,
   the actual created names are `<prefix>-<bucket-name>`, where `<prefix>` is
   set by the `prefix` variable in the `.tfvars` file

   `delete_after` specifies the number of days after *object creation
   time* the object will be automatically cleaned up - this is
   very helpful for 'scratch' buckets that are temporary. Set to
   `null` to prevent this cleaning up process from happening, e.g., if users want a persistent bucket.

   `archival_storageclass_after` (available only for AWS currently) transitions objects
   created in this bucket to a cheaper, slower archival class after the number of days
   specified in this variable. This is helpful for archiving user home directories or similar
   use cases, where data needs to be kept for a long time but rarely accessed. This should
   not be used for frequently accessed or publicly accessible data.

2. Enable access to these buckets from the hub or make them publicly accessible from outside
   by [editing `hub_cloud_permissions`](howto:features:cloud-access:access-perms)
   in the same `.tfvars` file. Follow all the steps listed there - this
   should create the storage buckets and provide all users access to them!

3. You can set the `SCRATCH_BUCKET` (and the deprecated `PANGEO_SCRATCH`)
   env vars on all user pods so users can use the created bucket without
   having to hard-code the bucket name in their code. In the hub-specific
   `.values.yaml` file in `config/clusters/<cluster-name>`,
   set:

   ```yaml
    jupyterhub:
      singleuser:
         extraEnv:
            SCRATCH_BUCKET: <s3 or gs>://<bucket-full-name>/$(JUPYTERHUB_USER)
            PANGEO_SCRATCH: <s3 or gs>://<bucket-full-name>/$(JUPYTERHUB_USER)
            # If we have a bucket that does not have a `delete_after`
            PERSISTENT_BUCKET: <s3 or gs>://<bucket-full-name>/$(JUPYTERHUB_USER)
            # If we have a bucket defined in user_buckets that should be granted public read access.
            PUBLIC_PERSISTENT_BUCKET: <s3 or gs>://<bucket-full-name>/$(JUPYTERHUB_USER)

   ```

   ```{note}
   Use s3 on AWS and gs on GCP for the protocol part
   ```
   ```{note}
   If the hub is a `daskhub`, nest the config under a `basehub` key
   ```

   The `$(JUPYTERHUB_USER)` expands to the name of the current user for
   each user, so everyone gets a little prefix inside the bucket to store
   their own stuff without stepping on other people's objects. But this is
   **not a security mechanism** - everyone can access everyone else's objects!

   `<bucket-full-name>` is the *full* name of the bucket, which is formed by
   `<prefix>-<bucket-name>`, where `<prefix>` is also set in the `.tfvars` file.
   You can see the full names of created buckets with `terraform output buckets`
   too.

   You can also add other env vars pointing to other buckets users requested.

4. Get this change deployed, and users should now be able to use the buckets!
   Currently running users might have to restart their pods for the change to take effect.

## Testing access to buckets

Once bucket access has been set up, we should test to make sure users can write
to and read from it.

### AWS

1. Login to the hub, and open a Terminal in JupyterLab

2. Look for the environment variables we just set (`SCRATCH_BUCKET` and/or `PERSISTENT_BUCKET`), make
   sure they are showing up correctly:

   ```bash
   env | grep _BUCKET
   ```

   They should end with the name of your JupyterHub user. For example, here is the output
   on the openscapes hub, when my JupyterHub username is `yuvipanda`:

   ```
   PERSISTENT_BUCKET=s3://openscapeshub-persistent/yuvipanda
   SCRATCH_BUCKET=s3://openscapeshub-scratch/yuvipanda
   ```

3. Check if the AWS CLI is installed by running the `aws` command - many base images
   already include this package. If not, you can do a local installation with:

   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   export PATH=$(pwd)aws/dist/:$PATH
   ```

   ```{note}
   This could have been as simple as a `pip install`, but [AWS does not support it](https://github.com/aws/aws-cli/issues/4947)
   ```

4. Create a temporary file, which we will then copy over to our scratch bucket.

   ```bash
   echo 'hi' > temp-test-file
   ```

5. Copy the file over to S3, under `$SCRATCH_BUCKET` or `$PERSISTENT_BUCKET` (based on
   which one we are going to be testing).

   ```bash
   aws s3 cp temp-test-file $SCRATCH_BUCKET/temp-test-file
   ```

   This should succeed with a message like `upload: ./temp-test-file to s3://openscapeshub-scratch/yuvipanda/temp-test-file`

6. Let's list our bucket to make sure the file is there.

   ```bash
   $ aws s3 ls $SCRATCH_BUCKET/
   2024-03-26 01:38:53          3 temp-test-file
   ```

   ```{note}
   The trailing `/` is important.
   ```

   ```{note}
   If testing `$PERSISTENT_BUCKET`, use that environment variable instead
   ```

7. Copy the file back from s3, to make sure we can read.

   ```bash
   $ aws s3 cp  $SCRATCH_BUCKET/temp-test-file back-here
   download: s3://openscapeshub-scratch/yuvipanda/temp-test-file to ./back-here
   $ cat back-here
   hi
   ```

   We have verified this all works!

8. Clean up our  files so we don't cost the community money in the long run.

   ```bash
   aws s3 rm $SCRATCH_BUCKET/temp-test-file
   rm temp-test-file back-here
   ```

## Allowing public, readonly to buckets from outside the JupyterHub

### GCP

Some hubs want to expose a particular bucket to the broad internet.
This can have catastrophic cost consequences, so we only allow this
on clusters where 2i2c is not paying the bill for.

This can be enabled by setting the `public_access` parameter in
`user_buckets` for the appropriate bucket, and running `terraform apply`.

Example:

```terraform
user_buckets = {
   "persistent": {
      "delete_after": null,
      "public_access": true
   }
}
```

## Enable access logs for objects in a bucket

### GCP

We may want to know *what* objects in a bucket are actually being accessed,
and when. While there is not a systematic way to do a 'when was this
object last accessed', we can instead enable [usage logs](https://cloud.google.com/storage/docs/access-logs)
that allow hub administrators to get access to some raw data.

Note that we currently can not actually help hub admins process these
logs - that is *their* responsibility. We can only *enable* this logging.

This can be enabled by setting `usage_logs` parameter in `user_buckets`
for the appropriate bucket, and running `terraform apply`.

Example:

```terraform
user_buckets = {
   "persistent": {
      "usage_logs": true
   }
}
```

Once enabled, you can find out what bucket the access logs will be sent
to with `terraform output usage_log_bucket`. The access logs will by
default be deleted after 30 days, to avoid them costing too much money.

The logs are in CSV format, with the fields [documented here](https://cloud.google.com/storage/docs/access-logs#format).
We suggest that hub admins interested can [download the logs](https://cloud.google.com/storage/docs/access-logs#downloading)
and parse them as they wish - this is not something that we can currently help
much with.

## Allowing authenticated access to buckets from outside the JupyterHub

### GCP

Some hub users want to be able to write to the bucket from outside the hub,
primarily for large data transfer from on-premise systems. Since
[Google Groups](https://groups.google.com) can be used to control access to
GCS buckets, it can be used to allow arbitrary users to write to the bucket!

1. With your `2i2c.org` google account, go to [Google Groups](https://groups.google.com) and create a new Google Group with the name
   "<bucket-name>-writers", where "<bucket-name>" is the name of the bucket
   we are going to grant write access to.

2. Grant "Group Owner" access to the community champion requesting this feature.
   They will be able to add / remove users from the group as necessary, and
   thus manage access without needing to involve 2i2c engineers.

3. In the `user_buckets` definition for the bucket in question, add the group
   name as an `extra_admin_members`:

   ```terraform
   user_buckets = {
     "persistent": {
       "delete_after": null,
       "extra_admin_members": [
         "group:<name-of-group>@googlegroups.com"
       ]
     }
   }
   ```

   Apply this terraform change to create the appropriate permissions for members
   of the group to have full read/write access to that GCS bucket.

4. We want the community champions to handle granting / revoking access to
   this google group, as well as produce community specific documentation on
   how to actually upload data here. We currently do not have a template of
   how end users can use this, but something can be stolen from the
   [documentation for LEAP users](https://leap-stc.github.io/leap-pangeo/jupyterhub.html#i-have-a-dataset-and-want-to-work-with-it-on-the-hub-how-do-i-upload-it)

## Granting access to cloud buckets in other cloud accounts / projects

Sometimes, users on a hub we manage need access to a storage bucket
managed by an external third party - often a different research
group. This can help with access to raw data, collaboration, etc.

This section outlines how to grant this access. Currently, this
functionality is implemented only on AWS - but we can add it for
other cloud providers when needed.

### AWS

On AWS, we would need to set up [cross account S3 access](https://aws.amazon.com/premiumsupport/knowledge-center/cross-account-access-s3/). It requires action from both the 2i2c engineering team as
well as the the community representative.

1. **Who**: 2i2c Engineering Team

   Find the ARN of the service account that is assumed by the users on the hub,
   under `userServiceAccount.annotations.eks.amazon.com/role-arn` in the YAML
   config specific to the hub. It should look something like
   `arn:aws:iam::<account-id>:role/<hub-name>`.

   If this hub has an equivalent *staging* hub, find the ARN of the service
   account for the staging hub too. This helps us keep staging and prod in sync.

2. **Who**: 2i2c Engineering Team

   Generate a [Bucket Policy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-iam-policies.html)
   that can be communicated to the community champion. You need to generate one policy
   for each ARN determined in step 1. The `Action` section lists various permissions to be
   granted. The default is to allow hub users to list all objects and get data - so readonly
   access. The community champion is welcome to modify this to fit their needs.

   ```json
   {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "<arn-of-service-account-from-step-1>"
            },
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<name-of-bucket>",
                "arn:aws:s3:::<name-of-bucket>/*"
            ]
        }
    ]
   }
   ```

   here,
   1. `Statement.Principal.AWS` is the ARN determined from step 1. This is the only item that needs
      to be supplied by the 2i2c engineer.
   2. `Statement.Action` is the list of S3 permissions to be granted. The default allows readonly
      access, with the ability to list objects and get their data. The community champion is welcome
      to modify this to fit their needs.
   3. `Statement.Resource` is the list of buckets this policy is applied to. There are two entries for
      each bucket, as some permissions apply to the bucket itself and some apply to the contents of
      the bucket. We don't need to know the list of buckets here, the community champion can supply this.

3. **Who**: 2i2c Engineering Team

   Communicate to the community champion that they need to [attach a bucket policy](https://docs.aws.amazon.com/AmazonS3/latest/userguide/add-bucket-policy.html)
   to the S3 buckets. You can use the following template.

   ```{note}
   To start the process, we need to attach policies to the appropriate S3 bucket to grant access
   to the hub. I've generated these templates:

   {{ JSON from step 2. Include multiple ones if we are doing this for multiple hubs }}

   {{ if a staging hub is included }}
   This includes access permissions for staging hub we use to test out changes to the main hub,
   so those two can be in sync.
   {{ end if }}

   You need to fill in the list of S3 buckets you want granted access under the "Resource" section.
   Note that there are two entries for each bucket.

   This policy, as written, will grant readonly access to the buckets from the hub. Users
   on the hub will be able to list objects and retrieve them. If you'd like to grant other
   kinds of access, adjust the list under 'Actions' accordingly.

   AWS has [some documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/add-bucket-policy.html)
   on how to attach this bucket policy. Once attached, can you give us the full content of the
   policy you attached? That would help us take next steps in granting access to these buckets.

   Thanks!
   ```

4. **Who**: Community Champion

   They attach the bucket policy, and get back to us with content of the policy they attached. This
   helps us see the list of buckets that are authorized, as well as a record of what permissions
   were actually granted.

5. **Who**: 2i2c Engineering Team

   In the `.tfvars` file for the cluster hosting the hub, add `extra_iam_policy`
   as a key to the hub under `hub_cloud_permissions`. This is used to set any additional
   IAM permissions granted to the users of the hub. In this case, we use `s3:*` to allow
   all S3 actions on the given list of buckets, so the exact permissions granted are
   controlled by the bucket policy set in earlier steps. This allows the community to grant
   more (or less) permissions in the future without any intervention on our part.

   ```json
   {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": [
                "arn:aws:s3:::<name-of-bucket>",
                "arn:aws:s3:::<name-of-bucket>/*"
            ]
        }
    ]
   }
   ```

6. **Who**: 2i2c Engineering Team

   Apply the terraform config, and test out if s3 bucket access works on the hub!
   If `s3:ListBucket` is among the granted permissions, you can test by running
   `aws s3 ls s3://<bucket-name>`. If it is *not* among the granted permissions,
   you need to ask the community for the full path of an object, so you can try to
   check for access with `aws s3 cp s3://<object-path> temp`, and seeing if it
   copied the object to `temp`
