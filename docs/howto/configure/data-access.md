# Data Access

Here we will document various ways to grant hubs access to external data.

## Data Access via Requester Pays

For some hubs, such as our Pangeo deployments, the communities they serve require access to data stored in other projects.
Accessing data normally comes with a charge that the folks _hosting_ the data have to take care of.
However, there is a method by which those making the request are responsible for the charges instead: [Requester Pays](https://cloud.google.com/storage/docs/requester-pays).
This section demonstrates the steps required to setup this method.

### Setting up Requester Pays Access on GCP

```{note}
We may automate these steps in the future.
```

Make sure you are logged into the `gcloud` CLI and have set the default project to be the one you wish to work with.

```{note}
These steps should be run every time a new hub is added to a cluster, to avoid sharing of credentials.
```

1. Create a new Service Account

```bash
gcloud iam service-accounts create {{ NAMESPACE }}-user-sa \
  --description="Service Account to allow access to external data stored elsewhere in the cloud" \
  --display-name="Requester Pays Service Account"
```

where:

- `{{ NAMESPACE }}-user-sa` will be the name of the Service Account, and;
- `{{ NAMESPACE }}` is the name of the deployment, e.g. `staging`.

```{note}
We create a separate service account for this so as to avoid granting excessive permissions to any single service account.
We may change this policy in the future.
```

2. Grant the Service Account roles on the project

We will need to grant the [Service Usage Consumer](https://cloud.google.com/iam/docs/understanding-roles#service-usage-roles) and [Storage Object Viewer](https://cloud.google.com/iam/docs/understanding-roles#cloud-storage-roles) roles on the project to the new service account.

```bash
gcloud projects add-iam-policy-binding \
  --role roles/serviceusage.serviceUsageConsumer \
  --member "serviceAccount:{{ NAMESPACE }}-user-sa@{{ PROJECT_ID }}.iam.gserviceaccount.com" \
  {{ PROJECT_ID }}

gcloud projects add-iam-policy-binding \
  --role roles/storage.objectViewer \
  --member "serviceAccount:{{ NAMESPACE }}-user-sa@{{ PROJECT_ID }}.iam.gserviceaccount.com" \
  {{ PROJECT_ID }}
```

where:

- `{{ PROJECT_ID }}` is the ID of the Google Cloud project, **not** the display name!
- `{{ NAMESPACE }}` is the deployment namespace

````{note}
If you're not sure what `{{ PROJECT_ID }}` should be, you can run:

```bash
gcloud config get-value project
```
````

3. Grant the Service Account the `workloadIdentityUser` role on the cluster

We will now grant the [Workload Identity User](https://cloud.google.com/iam/docs/understanding-roles#service-accounts-roles) role to the cluster to act on behalf of the users.

```bash
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:{{ PROJECT_ID }}.svc.id.goog[{{ NAMESPACE }}/{{ SERVICE_ACCOUNT }}]" \
  {{ NAMESPACE }}-user-sa@{{ PROJECT_ID }}.iam.gserviceaccount.com
```

Where:

- `{{ PROJECT_ID }}` is the project ID of the Google Cloud Project.
  Note: this is the **ID**, not the display name!
- `{{ NAMESPACE }}` is the Kubernetes namespace/deployment to grant access to
- `{{ SERVICE_ACCOUNT }}` is the _Kubernetes_ service account to grant access to.
  Usually, this is `user-sa`.
  Run `kubectl --namespace {{ NAMESPACE }} get serviceaccount` if you're not sure.

4. Link the Google Service Account to the Kubernetes Service Account

We now link the two service accounts together so Kubernetes can use the Google API.

```bash
kubectl annotate serviceaccount \
  --namespace {{ NAMESPACE }} \
  {{ SERVICE_ACCOUNT }} \
  iam.gke.io/gcp-service-account={{ NAMESPACE }}-user-sa@{{ PROJECT_ID }}.iam.gserviceaccount.com
```

Where:

- `{{ NAMESPACE }}` is the target Kubernetes namespace
- `{{ SERVICE_ACCOUNT }}` is the target Kubernetes service account name.
  Usually, this is `user-sa`.
  Run `kubectl --namespace {{ NAMESPACE }} get serviceaccount` if you're not sure.
- `{{ PROJECT_ID }}` is the project ID of the Google Cloud Project.
  Note: this is the **ID**, not the display name!

5. RESTART THE HUB

This is a very important step.
If you don't do this you won't see the changes applied.

You can restart the hub by heading to `https://{{ hub_url }}/hub/admin` (you need to be logged in as admin), clicking the "Shutdown Hub" button, and waiting for it to come back up.

You can now test the requester pays access by starting a server on the hub and running the below code in a script or Notebook.

```python
from intake import open_catalog

cat = open_catalog("https://raw.githubusercontent.com/pangeo-data/pangeo-datastore/master/intake-catalogs/ocean/altimetry.yaml")
ds = cat['j3'].to_dask()
```
