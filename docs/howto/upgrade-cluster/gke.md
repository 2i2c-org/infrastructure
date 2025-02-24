(upgrade-cluster:gke)=
# Upgrade Kubernetes cluster on GKE

## GKE's default upgrade policy

[standard cluster upgrades]: https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-upgrades

GKE has helpful documentation on how it handles [standard cluster upgrades].
Most notably, the default upgrade strategy is called "surge", which mimics what we refer to as "rolling upgrades" in other parts of our documentation.
The basic steps remain consistent but are handled automatically be GKE:

1. A node is cordoned so that new pods are not scheduled to it
1. The node is drained. For the surge strategy, `PodDisruptionBudget` and `GracefulTerminationPeriod` settings are respected for up to one hour.
1. The control plane reschedules pods managed by controllers onto other nodes. Pods that cannot be rescheduled remain in a Pending state until rescheduling is possible.

Due to these strategies, this means that changing the Kubernetes version via our terraform code produces a _non-destructive_ plan, i.e., the plan states that the nodes can be updated in place, rather than being destroyed and recreated.

## Upgrading a cluster

Setup your environment:

```bash
export CLUSTER_NAME=<cluster-name>
cd terraform/gcp
terraform init
terraforam workspace select $CLUSTER_NAME
```

### Zonal vs. regional clusters

- **Zonal clusters** only have one control plane in the defined zone. The control plane will be unavailable during upgrade, causing a short outage period (~5mins) where new pods representing new user servers will fail to be requested.
- **Regional clusters** have a control plane replica deployed in each zone associated with a region. Each control plane is updated sequentially meaning that the cluster remains highly available throughout the upgrade. Hence these upgrades take longer to roll out (~25mins).

### Check supported versions in terraform

There is a terraform output variable that provides the most up-to-date version supported by GKE for a range of predefined Kubernetes version prefixes:

```bash
terraform output regular_channel_latest_k8s_versions
```

You may wish to edit the prefixes checked in the [`variables.tf` file](https://github.com/2i2c-org/infrastructure/blob/44c94332ba8d40681d2f40c0860e99d6b6ca5e96/terraform/gcp/variables.tf#L43-L64).

(upgrade-cluster:gke:control-plane)=
### Upgrading the control plane

Within the `k8s_versions` block of the cluster's `.tfvars` file, increment the `min_master_version` variable according to the `regular_channel_latest_k8s_versions` output.

```
k8s_versions = {
  min_master_version : "1.32.1-gke.1357001",  # Increment this
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
}
```

Then plan and apply the changes:

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

When upgrading the control plane, it is best to upgrade one minor version at a time until you reach your desired version, e.g., 1.30 -> 1.31 -> 1.32.

### Upgrading node pools

The process for upgrading the worker node pools is very similar to that for [upgrading the control plane](upgrade-cluster:gke:control-plane).

First, upgrade the core node pool by updating the `core_nodes_version` variable in the `k8s_versions` block of the cluster's `.tfvars` file, and plan and apply the changes.

Then upgrade the server node pools by updating the `notebook_node_version` variable, and the `dask_nodes_version` variable if present, and plan and apply the changes.

Unlike with the control plane, you can jump straight from the current version to the desired version.
