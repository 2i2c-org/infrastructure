# Adding a new hub

This section describes steps around adding hubs to the 2i2c JupyterHub federation.

## Infrastructure that is needed for a hub

There are three kinds of infrastructure needed to add a new hub:

- **A Kubernetes cluster**.
  Deploying a Kubernetes cluster is specific to the cloud provider. For hubs that do not need to use their own cloud credits, or otherwise are fine running on a cloud project that is not owned by their institution, we can deploy hubs on an already-running Kubernetes Cluster.
  For hubs that require their own cluster, we'll need to set it up on our own with Terraform.
  To do so, see [new-cluster].
- **Support infrastructure**.
  This is a collection of services that run on a Kubernetes Cluster and help us in running and monitoring things.
  There is one set of services running per **cluster**, not per hub.
  This includes things like Grafana, NFS server provisioners, etc.
- **JupyterHubs**.
  When a cluster is up and running, we may then deploy JupyterHubs on top of it using the JupyterHub Helm Chart.
  This is generally controlled via configuration in the `pilot-hubs/` repository, and GitHub actions that automatically deploy new hubs (or modify existing ones) on a cluster.
  There are some cases where you must manually deploy or modify a hub.
  See [](operate:manual-deploy) for more details.

## When to deploy a new cluster

Deploying a new cluster is a more complex and costly operation, and generally requires more of our time to upkeep and deploy (and thus, will be more costly to the community).
In general, we'd like hubs to be deployed on pre-existing clusters whenever possible, rather than having a dedicated cluster that is just for the hub's community.

In general, the question of whether to deploy a new cluster for a community comes down to **whether they need to use their own cloud billing accounts**. This is usually either because they have their own cloud credits that they wish to use, or because they work at an institution that mandates (or otherwise incentivizes) individuals to use institutional cloud accounts.

For most hub communities that simply wish to pay for a hub and are not opinionated about the cluster on which it runs, we can deploy their hub on a pre-existing Kubernetes cluster.

## Automated vs. manual deploys

Some of our infrastructure automatically deploys and updates hubs via GitHub Workflows, while others require manual deploys.
This is changing over time as we automate more things, and is dependent on the cloud provider.
See the sections below for information about deploying hubs on each cloud provider, including whether to manually or automatically deploy.



## Process for deploying a new hub

We use a GitHub Issue Template to keep track of the to-do items in creating a new hub.
The best way to understand the information and steps needed for this process is in that template.
Below is a short overview of the steps in the process.

1. [Create a new GitHub issue for the hub](https://github.com/2i2c-org/pilot-hubs/issues/new?assignees=&labels=type%3A+hub&template=2_new-hub.yml&title=New+Hub%3A+%3CHub+name%3E).
   The following steps are major sections described in the template.
2. Collect information about the hub that helps us deploy it in the proper manner (see the issue template for explanations about the information we need).
3. Create the hub via appending a new hub entry in the appropriate cluster file under
   `config/hubs` file (see [](/topic/config.md) for more information).
4. Start following [team process](team-process) around operating the hubs.

## Cloud provider-specific information

The following sections contain information that is unique to each cloud provider.
Follow these guides in addition to the more general instructions above.

```{toctree}
add-aws-hub.md
```
