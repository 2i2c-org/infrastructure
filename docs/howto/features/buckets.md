(howto:features:cloud-access:storage-buckets)=
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

2. Enable access to these buckets from the hub by [editing `hub_cloud_permissions`](howto:features:cloud-access:access-perms)
   in the same `.tfvars` file. Follow all the steps listed there - this
   should create the storage buckets and provide all users access to them!

3. (If requested) Enable public read access to these buckets by editing the
   `bucket_public_access` list in the same `.tfvars`:

   ```terraform
   bucket_public_access = [
      "public-persistent"
   ]
   ```

4. You can set the `SCRATCH_BUCKET` (and the deprecated `PANGEO_SCRATCH`)
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

5. Get this change deployed, and users should now be able to use the buckets!
   Currently running users might have to restart their pods for the change to take effect.