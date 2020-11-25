# Operating the hubs

Information about operating the hubs, debugging problems, and performing common actions.

## Gain `kubectl` & `helm` access to a hub

Each of the hubs in the 2i2c Pilot runs on Google Cloud Platform and Kubernetes.
To access the Kubernetes objects (in order to inspect them or make changes), use
the `kubectl` command line tool. You can also use `helm` to 

### Project Access

First, you'll need to access the Google Cloud projects on which the hubs run. The most accurate name
of the project can be gleamed from `hubs.yaml` (under `gcp.project` for each cluster entry). Currently,
the projects are:

| Cluster | Project Name |
| - | - |
| *.pilot.2i2c.cloud | `two-eye-two-see` |
| *.cloudbank.2i2c.cloud | `cb-1003-1696` |

If you don't have access to these, please get in touch with 2i2c staff.

### Commandline tools installation

You can do all this via [Google Cloud Shell](https://cloud.google.com/shell),
but might be easier to do this on your local machine. You'll need the following
tools installed:

1. [gcloud](https://cloud.google.com/sdk)
2. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
3. [helm](https://helm.sh/)

### Authenticating

First, you need to [gcloud auth login](https://cloud.google.com/sdk/docs/authorizing#authorizing_with_a_user_account),
so you can perform `gcloud` operations. Next, you need to do [gcloud auth application-default login](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
so `kubectl` and `helm` could use your auth credentials.

### Fetch Cluster credentials

For each cluster, you'll need to fetch credentials at least once with [gcloud container clusters get-credentials](https://cloud.google.com/sdk/gcloud/reference/container/clusters/get-credentials).

```bash
gcloud container clusters get-credentials <cluster-name> --region <region> --project <project-name>
```

You can get authoritative information for `<cluster-name>`, `<zone>` and `<project-name>` from
`hubs.yaml`.

With that, `kubectl` and `helm` should now work! 

### (Optional) Access via Google Cloud Shell

Instead of setting up the tools & authenticating locally, you can do all this via
[Google Cloud Shell](https://cloud.google.com/shell). It has all the tools installed,
and the authentication done. Instead of doing `gcloud container clusters get-credentials`
yourself, you can instead:


1. Go to the [Google Cloud Kubernetes Engine page](https://console.cloud.google.com/kubernetes/list) (for the appropriate project)

2. Click on `Connect`, as seen in the figure below.

   ````{panels}
   ```{figure} images/gcp-k8s-dashboard.png
   ```
   ---
   ```{figure} images/gcp-run-in-shell.png
   ```
   ````

3. This will spin up an interactive cloud shell where you have `kubectl` access.

## Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.
2. **Backup the home directory contents**. Especially if we think that users will want this information in the future (or if we plan to re-deploy a hub elsewhere).
3. **Delete the Helm namespace**. Run `helm -n <hub-name> delete <hub-name>`.
4. **Delete our Authentication entry**. If the hub hasn't been recreated anywhere, remove the entry from `auth0.com`

## Access the Hub Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

The Grafana for each cluster can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the pilot hubs are accessible at `grafana.pilot.2i2c.cloud`. You'll need
a username and password to access each one. Ask one of the 2i2c team members for access.
