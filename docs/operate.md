# Operating the hubs

Information about operating the hubs, debugging problems, and performing common actions.

## Gain `kubectl` access to a hub

Each of the hubs in the 2i2c Pilot runs on Google Cloud Platform and Kubernetes. To access the Kubernetes deployments (in order to inspect them or make changes), use the `kubectl` command line tool.

In order to get this tool and ensure that it works, first ensure **ensure your Google account is added to the `two-eye-two-see` hubs project.** If you aren't sure, ask one of the hub administrators to determine if this is the case.

Next, go to the Google Cloud Kubernetes configuration page for this project (at the following URL):

<https://console.cloud.google.com/kubernetes/list?project=two-eye-two-see>`

Click on `Connect`, as seen in the figure below.

````{panels}
```{figure} images/gcp-k8s-dashboard.png
```
---
```{figure} images/gcp-run-in-shell.png
```
````

This will spin up an interactive cloud shell where you have `kubectl` access to the `two-eye-two-see` hub infrastructure.

:::{admonition,tip} Working locally with the CLI
If you'd like to work locally, you may also install the `kubectl` and `helm` CLIs locally. To do so, follow the [steps from the Z2JH guide](https://zero-to-jupyterhub.readthedocs.io/en/latest/kubernetes/google/step-zero-gcp.html#kubernetes-on-google-cloud-gke) (begin with "choose a terminal"). When that is done, copy and run the "Command-line access" command that is shown on the "Connect to the cluster" page. It is something like:

```
gcloud container clusters get-credentials low-touch-hubs-cluster --region us-central1 --project two-eye-two-see
```

You may need to authenticate your local CLI with Google Cloud first with `gcloud auth login`.
:::


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
