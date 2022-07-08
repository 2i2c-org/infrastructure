# Enable user access to cloud features

Users of our hubs often need to be granted specific cloud permissions
so they can use features of the cloud provider they are on, without
having to do a bunch of cloud-provider specific setup themselves. This
helps keep code cloud provider agnostic as much as possible, while also
improving the security posture of our hubs.

This page lists various features we offer around access to cloud resources,
and how to enable them.

## How it works

### GCP

On Google Cloud Platform, we use [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
to map a particular [Kubernetes Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
to a particular [Google Cloud Service Account](https://cloud.google.com/iam/docs/service-accounts).
All pods using the Kubernetes Service Account (user's jupyter notebook pods
as well as dask worker pods)
will have the permissions assigned to the Google Cloud Service Account.
This Google Cloud Service Account is managed via terraform.

### AWS

On AWS, we use [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
to map a particular [Kubernetes Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
to a particular [AWS IAM Role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html).
All pods using the Kubernetes Service Account (user's jupyter notebook pods
as well as dask worker pods)
will have the permissions assigned to the AWS IAM Role.
This AWS IAM Role is managed via terraform.


(howto:features:cloud-access:access-perms)=
## Enabling specific cloud access permissions

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
   2. (GCP only) `requestor_pays` enables permissions for user pods and dask worker
      pods to identify as the project while making requests to Google Cloud Storage
      buckets marked as 'requestor pays'. More details [here](topic:features:cloud:gcp:requestor-pays).
   3. `bucket_admin_access` lists bucket names (as specified in `user_buckets`
      terraform variable) all users on this hub should have full read/write
      access to. Used along with the [user_buckets](howto:features:cloud-access:storage-buckets)
      terraform variable to enable the [scratch buckets](topic:features:cloud:scratch-buckets)
      feature.
   3. (GCP only) `hub_namespace` is the full name of the hub, as hubs are put in Kubernetes
      Namespaces that are the same as their names. This is explicitly specified here
      because `<hub-name-slug>` could possibly be truncated on GCP.

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

   ```{tabbed} GCP
   <pre>
   $ terraform output kubernetes_sa_annotations
   {
     "prod" = "iam.gke.io/gcp-service-account: meom-ige-prod@meom-ige-cnrs.iam.gserviceaccount.com"
     "staging" = "iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
   }
   </pre>
   ```

   ```{tabbed} AWS
   <pre>
   $ terraform output kubernetes_sa_annotations
   {
     "prod" = "eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-prod"
     "staging" = "eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-staging"
   }
   </pre>
   ```

   This shows all the annotations for all the hubs configured to provide cloud access
   in this cluster. You only need to care about the hub you are currently dealing with.

5. (If needed) create a `.values.yaml` file specific to this hub under `config/clusters/<cluster-name>`,
   and add it under `helm_chart_values_files` for the appropriate hub in `config/clusters/<cluster-name>/cluster.yaml`.

6. Specify the annotation from step 4, nested under `userServiceAccount.annotations`.

   ```{tabbed} GCP
    <pre>
    userServiceAccount:
        annotations:
            iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
   </pre>
    ```

   ```{tabbed} AWS
    <pre>
    userServiceAccount:
        annotations:
            eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-staging
   </pre>
    ```

    ```{note}
    If the hub is a `daskhub`, nest the config under a `basehub` key
    ```

7. Get this change deployed, and users should now be able to use the requestor pays feature!
   Currently running users might have to restart their pods for the change to take effect.

(howto:features:cloud-access:storage-buckets)=
## Creating storage buckets for use with the hub

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
   `null` to prevent this cleaning up process from happening.

2. Enable access to these buckets from the hub by [editing `hub_cloud_permissions`](howto:features:cloud-access:access-perms)
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
            SCRATCH_BUCKET: <s3 or gcs>://<bucket-full-name>/$(JUPYTERHUB_USER)
            PANGEO_SCRATCH: <s3 or gcs>://<bucket-full-name>/$(JUPYTERHUB_USER)
   ```

   ```{note}
   Use s3 on AWS and gcs on GCP for the protocol part
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
