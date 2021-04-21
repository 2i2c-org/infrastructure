# Gain `kubectl` & `helm` access to a hub

Each of the hubs in the 2i2c Pilot runs on Google Cloud Platform and Kubernetes.
To access the Kubernetes objects (in order to inspect them or make changes), use
the `kubectl` command line tool.

% TODO: Add something about what helm does here

## Project Access

First, you'll need to access the Google Cloud projects on which the hubs run. You
can find the current list of active projects by examining the `gcp.project`
values in the files under `config/hubs/*.cluster.yaml`.

## Commandline tools installation

You can do all this via [Google Cloud Shell](https://cloud.google.com/shell),
but might be easier to do this on your local machine. You'll need the following
tools installed:

1. [gcloud](https://cloud.google.com/sdk)
2. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
3. [helm](https://helm.sh/)

## Authenticating

First, you need to [gcloud auth login](https://cloud.google.com/sdk/docs/authorizing#authorizing_with_a_user_account),
so you can perform `gcloud` operations. Next, you need to do [gcloud auth application-default login](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
so `kubectl` and `helm` could use your auth credentials.

## Fetch Cluster credentials

For each cluster, you'll need to fetch credentials at least once with [gcloud container clusters get-credentials](https://cloud.google.com/sdk/gcloud/reference/container/clusters/get-credentials).

```bash
gcloud container clusters get-credentials <cluster-name> --region <region> --project <project-name>
```

You can get authoritative information for `<cluster-name>`, `<zone>` and `<project-name>` from
files under `config/hubs`.

With that, `kubectl` and `helm` should now work! 

## (Optional) Access via Google Cloud Shell

Instead of setting up the tools & authenticating locally, you can do all this via
[Google Cloud Shell](https://cloud.google.com/shell). It has all the tools installed,
and the authentication done. Instead of doing `gcloud container clusters get-credentials`
yourself, you can instead:


1. Go to the [Google Cloud Kubernetes Engine page](https://console.cloud.google.com/kubernetes/list) (for the appropriate project)

2. Click on `Connect`, as seen in the figure below.

   ````{panels}
   ```{figure} ../../images/gcp-k8s-dashboard.png
   ```
   ---
   ```{figure} ../../images/gcp-run-in-shell.png
   ```
   ````

3. This will spin up an interactive cloud shell where you have `kubectl` access.
