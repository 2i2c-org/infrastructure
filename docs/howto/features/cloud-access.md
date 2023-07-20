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
           bucket_public_access : ["bucket-1"]
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
      access to. Used along with the [user_buckets](howto:features:storage-buckets)
      terraform variable to enable the [scratch buckets](topic:features:cloud:scratch-buckets)
      feature.
   4. `bucket_public_access` lists bucket names (as specified in `user_buckets`
      terraform variable) that should be publicly accessible.
   5. (GCP only) `hub_namespace` is the full name of the hub, as hubs are put in Kubernetes
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

   `````{tab-set}
   ````{tab-item} GCP
   :sync: gcp-key
   ```bash
   $ terraform output kubernetes_sa_annotations
   {
     "prod" = "iam.gke.io/gcp-service-account: meom-ige-prod@meom-ige-cnrs.iam.gserviceaccount.com"
     "staging" = "iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
   }
   ```
   ````

   ````{tab-item} AWS
   :sync: aws-key
   ```bash
   $ terraform output kubernetes_sa_annotations
   {
     "prod" = "eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-prod"
     "staging" = "eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-staging"
   }
   ```
   ````
   `````

   This shows all the annotations for all the hubs configured to provide cloud access
   in this cluster. You only need to care about the hub you are currently dealing with.

5. (If needed) create a `.values.yaml` file specific to this hub under `config/clusters/<cluster-name>`,
   and add it under `helm_chart_values_files` for the appropriate hub in `config/clusters/<cluster-name>/cluster.yaml`.

6. Specify the annotation from step 4, nested under `userServiceAccount.annotations`.

   `````{tab-set}
   ````{tab-item} GCP
   :sync: gcp-key
   ```yaml
   userServiceAccount:
     annotations:
       iam.gke.io/gcp-service-account: meom-ige-staging@meom-ige-cnrs.iam.gserviceaccount.com"
   ```
   ````

   ````{tab-item} AWS
   :sync: aws-key
   ```yaml
   userServiceAccount:
     annotations:
       eks.amazonaws.com/role-arn: arn:aws:iam::740010314650:role/uwhackweeks-staging
   ```
   ````
   `````

    ```{note}
    If the hub is a `daskhub`, nest the config under a `basehub` key
    ```

7. Get this change deployed, and users should now be able to use the requestor pays feature!
   Currently running users might have to restart their pods for the change to take effect.

