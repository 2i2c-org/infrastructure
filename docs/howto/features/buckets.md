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
  
