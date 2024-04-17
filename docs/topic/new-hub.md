(new-hub)=
# Deploy a new hub

This section describes what adding hubs to the 2i2c JupyterHub federation is about from an infrastructure point of view.

## Infrastructure that is needed for a hub

There are three kinds of infrastructure needed to add a new hub. In most cases, they are configured via configuration in the `infrastructure/` repository.

- **A Kubernetes cluster**.
  Deploying a Kubernetes cluster is specific to the cloud provider. For hubs that do not need to use their own cloud credits, or otherwise are fine running on a cloud project that is not owned by their institution, we can deploy hubs on an already-running Kubernetes Cluster.
  For hubs that require their own cluster, we'll need to set it up on our own.
  To do so, see [](new-cluster).
- **Support infrastructure**.
  This is a collection of services that run on a Kubernetes Cluster and help us in running and monitoring things.
  There is one set of services running per **cluster**, not per hub.
  This includes things like Grafana, NFS server provisioners, etc.
  To setup this infrastructure, see [](support-components).
- **JupyterHubs**.
  When a cluster is up and running, we may then deploy JupyterHubs on top of it using the JupyterHub Helm Chart.
  Configuration that is specific to each JupyterHub is stored in the [`config/clusters`](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters) folder.
  A GitHub Action workflow then deploys and updates the hubs on a cluster using this configuration.
  There are some cases where you must manually deploy or modify a hub.
  See [](hubs:manual-deploy) for more details.

## Overview of hub configuration

Many of our hubs are automatically deployed and updated using GitHub Action workflows and configuration that is defined in [`infrastructure/config/clusters`](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters).

These are a collection of folders (one per cluster) that contain a collection of YAML files (one per hub deployed to that cluster, plus a cluster-wide file) that define the configuration for all of our hubs.
To learn which subset of clusters are *automatically* deployed via GitHub Actions, inspect the `matrix.cluster_name` list in [the `deploy-hubs.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/f2ffc8ef51427d5f824747917bfd51533daf3045/.github/workflows/deploy-hubs.yaml#L17-L31).

The process of automatically updating and adding hubs is almost the same for all of the hubs deployed on these clusters.

(hub-deployment)=
## Automated vs. manual deploys

Some of our infrastructure automatically deploys and updates hubs via GitHub Actions workflows, while others require manual deploys.
This is changing over time as we automate more things, and is dependent on the cloud provider.

General details about our CI/CD machinery lives at [](/reference/ci-cd/index.md)

### Deploying hubs manually

Some of our infrastructure still requires manual deploys.
There are also situations where you may want to deploy infrastructure manually.
Or situation where some specific steps still need some manual intervention.

The following sections cover how to deploy in these situations:

- [General manual deployment process](hubs:manual-deploy)

```{warning}
Manual deploys should be avoided when possible.
They increase the likelihood of confusion, bottlenecks of information, inconsistent
states and discrepancies between what is already deployed vs. the codebase, among other
things.
```
