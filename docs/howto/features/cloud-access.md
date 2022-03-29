# Enable user access to cloud features

Users of our hubs often need to be granted specific cloud permissions
so they can use features of the cloud provider they are on, without
having to do a bunch of cloud-provider specific setup themselves. This
helps keep code cloud provider agnostic as much as possible, while also
improving the security posture of our hubs.

This page lists various features we offer around access to cloud resources,
and how to enable them.

## GCP

### How it works

On Google Cloud Platform, we use [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
to map a particular [Kubernetes Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
to a particular [Google Cloud Service Account](https://cloud.google.com/iam/docs/service-accounts).
All pods using the Kubernetes Service Account (user's jupyter notebook pods
as well as dask worker pods)
will have the permissions assigned to the Google Cloud Service Account.
This Google Cloud Service Account is managed via terraform.

(howto:features:cloud-access:gcp:access-perms)=
### Enabling specific cloud access permissions

1. In the `.tfvars` file for the project in which this hub is based off
   create (or modify) the `hub_cloud_permissions` variable. The config is
   like:

   ```
   hub_cloud_permissions = {
       "<hub-name-slug>": {
           requestor_pays : true,
           bucket_admin_access : ["bucket-1", "bucket-2"]
           hub_namespace : "<hub-name>"
       }
   }
   ```

   where:

   1. `<hub-name-slug>` is the name of the hub, but restricted in length. This
      and the cluster name together can't be more than 29 characters. `terraform`
      will complain if you go over this limit, so in general just use the name
      of the hub and shorten it only if `terraform` complains.
   2. `requestor_pays` enables permissions for user pods and dask worker
      pods to identify as the project while making requests to Google Cloud Storage
      buckets marked as 'requestor pays'. More details [here](topic:features:cloud:gcp:requestor-pays).
   3. `bucket_admin_access` lists bucket names (as specified in `user_buckets`
      terraform variable) all users on this hub should have full read/write
      access to. Used along with the [user_buckets](howto:features:cloud-access:gcp:storage-buckets)
      terraform variable to enable the [scratch buckets](topic:features:cloud:gcp:scratch-buckets)
      feature.
   3. `hub_namespace` is the full name of the hub, as hubs are put in Kubernetes
      Namespaces that are the same as their names. This is explicitly specified here
      because `<hub-name-slug>` could possibly be truncated.

2. Run `terraform apply -var-file=projects/<cluster-var-file>.tfvars`, and look at the
   plan carefully. It should only be creating or modifying IAM related objects (such as roles
   and service accounts), and not really touch anything else. When it looks good, accept
   the changes and apply it. This provisions a Google Cloud Service Account (if needed)
   and grants it the appropriate permissions.

3. We will need to connect the Kubernetes Service Account used by the jupyter and dask pods
   with this Google Cloud Service Account. This is done by setting an annotation on the
   Kubernetes Service Account.

4. Run `terraform output kubernetes_sa_annotations`, this should
   show you a list of hubs and the annotation required to be set on them:

   ```
   $ terraform output kubernetes_sa_annotations
   {
    "prod" = "iam.gke.io/gcp-service-account: meom-ige-prod@meom-ige-cnrs.iam.gserviceaccount.com"
    "staging" = "iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
   }
   ```

   This shows all the annotations for all the hubs configured to provide cloud access
   in this cluster. You only need to care about the hub you are currently dealing with.

5. (If needed) create a `.values.yaml` file specific to this hub under `config/clusters/<cluster-name>`,
   and add it under `helm_chart_values_files` for the appropriate hub in `config/clusters/<cluster-name>/cluster.yaml`.

6. Specify the annotation from step 4, nested under `userServiceAccount.annotations`.

   ```yaml
    userServiceAccount:
        annotations:
            iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
    ```

    ```{note}
    If the hub is a `daskhub`, nest the config under a `basehub` key
    ```

7. Get this change deployed, and users should now be able to use the requestor pays feature!
   Currently running users might have to restart their pods for the change to take effect.

(howto:features:cloud-access:gcp:storage-buckets)=
### Creating storage buckets for use with the hub

See [the relevant topic page](topic:features:cloud:gcp:scratch-buckets) for
users want this!

1. In the `.tfvars` file for the project in which this hub is based off
   create (or modify) the `user_buckets` variable. The config is
   like:

   ```terraform
   user_buckets = ["bucket1", "bucket2"]
   ```

   Since storage buckets need to be globally unique across all of Google Cloud,
   the actual created names are `<prefix>-<bucket-name>`, where `<prefix>` is
   set by the `prefi` variable in the `.tfvars` file

2. Enable access to these buckets from the hub by [editing `hub_cloud_permissions`](howto:features:cloud-access:gcp:access-perms)
   in the same `.tfvars` file. Follow all the steps listed there - this
   should create the storage buckets and provide all users access to them!

3. You can set the `SCRATCH_BUCKET` (and the deprecated `PANGEO_SCRATCH`)
   env vars on all user pods so users can use the created bucket without
   having to hard-code the bucket name in their code. In the hub-specific
   `.values.yaml` file in `config/clusters/<cluster-name>/<hub-name>.values.yaml`,
   set:

   ```yaml
    jupyterhub:
      singleuser:
         extraEnv:
            SCRATCH_BUCKET: gcs://<bucket-name>/$(JUPYTERHUB_USER)
   ```

   ```{note}
   If the hub is a `daskhub`, nest the config under a `basehub` key
   ```

   The `$(JUPYTERHUB_USER)` expands to the name of the current user for
   each user, so everyone gets a little prefix inside the bucket to store
   their own stuff without stepping on other people's objects. But this is
   **not a security mechanism** - everyone can access everyone else's objects!

    You can also add other env vars pointing to other buckets users requested.

4. Get this change deployed, and users should now be able to use the buckets!
   Currently running users might have to restart their pods for the change to take effect.
