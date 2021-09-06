# Pangeo Data Access via Requestor Pays

https://cloud.google.com/storage/docs/requester-pays

```{note}
We may automate this in the future
```

## Steps to take on GCP

1. Create a Service Account

```bash
gcloud iam service-accounts create requestor-pays-sa \
  --description="Service Account to allow access to Pangeo data stored in the cloud" \
  --display-name="Requestor Pays Service Account"
```

where `requestor-pays-sa` will be the name of the Service Account.

2. Assign Roles and Policy Bindings

```bash
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[CLUSTER_NAME/NAMESPACE]" \
  requestor-pays-sa@PROJECT_ID.iam.gserviceaccount.com
```

Where:

- `PROJECT_ID` is the project ID of the Google Cloud Project.
  Note: this is the **ID**, not the display name!
- `CLUSTER_NAME` is the name of the cluster to grant access to.
- `NAMESPACE` is the Kubernetes namespace/deployment to grant access to.

3. Link the Google Service Account to the Kubernetes Service Account

```bash
kubectl annotate serviceaccount \
  --namespace NAMESPACE \
  SERVICE_ACCOUNT_NAME \
  iam.gke.io/gcp-service-account=requestor-pays-sa@PROJECT_ID.iam.gserviceaccount.com
```

Where:

- `NAMESPACE` is the target Kubernetes namespace
- `SERVICE_ACCOUNT_NAME` is the target Kubernetes service account name.
  Usually, this is `user-sa`.
  Run `kubectl --namespace NAMESPACE get serviceaccount` if you're not sure.
- `PROJECT_ID` is the project ID of the Google Cloud Project.
  Note: this is the **ID**, not the display name!
