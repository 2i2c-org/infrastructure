(new-hub)=
# Deploy a new hub

This section describes steps around adding hubs to the 2i2c JupyterHub federation.

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

(new-hub:deploy)=
## To add a new hub

To deploy a new hub, follow these steps:

1. Make sure a [`New Hub - Provide Information`](https://github.com/2i2c-org/infrastructure/issues/new?assignees=&labels=type%3A+hub&template=2_new-hub-provide-info.yml&title=%Provide+Information%5D+New+Hub%3A+%7B%7B+HUB+NAME+%7D%7D) issue was created and filled in with enough information from the Community Representative.
   Once that issue is created, move to the next step.
2. If no option was explicitly asked by the Community Representative, decide whether you'll deploy on a pre-existing Kubernetes cluster, or if you'll need to create a new one.
   See [](cluster:when-to-deploy) for information to help you decide.
3. Determine the **hub helm chart** that is needed.
   Hub helm charts are pre-configured deployments for certain kinds of JupyterHubs.
   There are a few base charts to choose from.
   For more information about our hub helm charts and how to choose, see [](hub-helm-charts).
4. Add a configuration entry for your new hub by creating a new `<hub_name>.values.yaml` file under the appropriate cluster folder, and referencing this file in a new entry under the `hubs` key in the cluster's `cluster.yaml` file.
   Each `*.values.yaml` file is a Zero to JupyterHub configuration, and you can customize whatever you like.
   The easiest way to add new configuration is to look at the entries for similar hubs under the same cluster folder, copy / paste one of them, and make modifications as needed for this specific hub.
   For example, see the hubs configuration in [the 2i2c Google Cloud cluster configuration directory](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/2i2c).

   ```{seealso}
   See [](/topic/infrastructure/config.md) for general information about hub helm chart configuration.
   ```

   ```{seealso}
   During this process you will likely also need to configure an Authentication Provider for the hub.
   See [](enable-auth-provider) for steps on how to achieve this.
   ```

   ```{seealso}
   At this point, you should have everything you need to deploy a hub that matches the requirements of the Community Representative.
   If however a specific feature has been requested that does not come out-of-the-box with `basehub` or `daskhub`, see [](hub-features) for information on how to deploy it and the relevant config that should be added to the `<hub>.values.yaml` file.
   ```

5. Make sure you setup the [PersistentVolume](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) in the hub's config.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key

An [EFS instance](https://aws.amazon.com/efs/) to store the hub home directories, should exist from when the cluster was created.

Get the address a hub on this cluster should use for connecting to NFS with
`terraform output nfs_server_dns`, and set it in the hub's config under
`nfs.pv.serverIP` (nested under `basehub` when necessary) in the appropriate
`<hub>.values.yaml` file.

```yaml
nfs:
   enabled: true
      enabled: false
   pv:
      enabled: true
      # from https://docs.aws.amazon.com/efs/latest/ug/mounting-fs-nfs-mount-settings.html
      mountOptions:
      - rsize=1048576
      - wsize=1048576
      - timeo=600
      - soft # We pick soft over hard, so NFS lockups don't lead to hung processes
      - retrans=2
      - noresvport
      serverIP: <from-terraform>
      baseShareName: /
```
````

````{tab-item} Google Cloud
:sync: gcp-key
```yaml
nfs:
  enabled: true
  pv:
    enabled: true
    mountOptions:
      - soft
      - noatime
    # Google FileStore IP
    serverIP: <gcp-filestore-ip>
    # Name of Google Filestore share
    baseShareName: /homes/
```
````

````{tab-item} Azure
:sync: azure-key
N/A
````
`````

6. Create a Pull Request with the new hub entry, and get a team member to review it.
7. Once you merge the pull request, the GitHub Action workflow will detect that a new entry has been added to the configuration file.
   It will then deploy a new JupyterHub with the configuration you've specified onto the corresponding cluster.
8. Monitor the action to make sure that it completes.
   If something goes wrong and the workflow does not finish, try [deploying locally](hubs:manual-deploy) to access the logs to help understand what is going on.
   It may be necessary to make new changes to the hub's configuration via a Pull Request, or to *revert* the old Pull Request if you cannot determine how to resolve the problem.

   ```{attention}
   In order to protect sensitive tokens, our CI/CD pipeline will **not** print testing output to its logs.
   You will need to run the [health check locally](hubs:manual-deploy:health-check) to inspect these logs.
   ```

9. Log in to the hub and ensure that the hub works as expected from a user's perspective.
10. Send a link to the hub's Community Representative(s) so they can confirm that it works from their perspective as well.

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
