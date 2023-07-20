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
   
   
## Allowing access to buckets from outside the JupyterHub

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

On AWS, we would need to set up [cross account S3 access](https://aws.amazon.com/premiumsupport/knowledge-center/cross-account-access-s3/).

1. Find the ARN of the service account used by the *users* on the hub. You can
   find this under `userServiceAccount.annotations.eks.amazon.com/role-arn` in
   the `values.yaml` file for your hub. It should look something like
   `arn:aws:iam::<account-id>:role/<hub-name>`.
2. In the AWS account *with the S3 bucket*, [create an IAM
   policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html)
   that grants appropriate access to the S3 bucket from the hub. For example, the
   following policy grants readonly access to the bucket for users of the hub

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

   You can add additional permissions to the bucket if needed here.

   ```{note}
   You can list as many buckets as you want, but each bucket needs two entries -
   one with the `/*` and one without so both listing the bucket as well as fetching
   data from it can work
   ```

3. In the `.tfvars` file for the cluster hosting the hub, add `extra_iam_policy`
   as a key to the hub under `hub_cloud_permissions`. This is used to set any additional
   IAM permissions granted to the users of the hub. In this case, you should copy the
   exact policy that was applied to the bucket in step 2, but remove the "Principal" key.
   So it would look something like:

   ```json
   {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
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

4. Apply the terraform config, and test out if s3 bucket access works on the hub!
