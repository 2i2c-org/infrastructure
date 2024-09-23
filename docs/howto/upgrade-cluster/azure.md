(upgrade-cluster:azure)=
# Upgrade Kubernetes cluster on Azure

## Cluster upgrade

### 1. Prepare two terminal sessions

Start two terminal sessions and run `export CLUSTER_NAME=...` in both.

In the first terminal...:

1. Change into the Azure terraform directory `cd terraform/azure`
1. Run `az login` and authenticate with the account associated with the cluster to be upgraded.

```{note}
We currently only have two Azure clusters: UToronto and PChub.
Each team member should have a UToronto admin account of their own, whereas the credentials for the PChub account are in the shared Bitwarden.
```

In the second terminal, setup k8s credentials with:

```bash
deployer use-cluster-credentials $CLUSTER_NAME
```

### 2. Check cluster status and activity

Before upgrading, get a sense of the current status of the cluster and users
activity in it.

```bash
# get nodes, and k8s version, and their node group names
# - what node groups are active currently?
kubectl get node --label-columns=kubernetes.azure.com/agentpool

# get all pods
# - are there any non-running/non-ready pod with issues before upgrading?
kubectl get pod -A

# get users' server and dask cluster pods
# - how many user servers are currently running?
# - is this an acceptable time to upgrade?
kubectl get pod -A -l "component=singleuser-server"
kubectl get pod -A -l "app.kubernetes.io/component in (dask-scheduler, dask-worker)"
```

### 3. Get the latest supported k8s versions from terraform

We have a terraform output variable that tells us the latest supported k8s version for Azure Kubernetes Service.
Use this to establish which version to upgrade to.

```bash
terraform output latest_supported_k8s_versions
```

```{note}
You may need a to run a terraform plan and apply first to ensure this variable is up-to-date.

You can also control which minor k8s versions terraform will check using the `k8s_version_prefixes` variable defined in the [`variables.tf` file](https://github.com/2i2c-org/infrastructure/blob/HEAD/terraform/azure/variables.tf).
```

### 4. Upgrade the k8s control plane

#### 4.1. Upgrade the k8s control plane one minor version

The k8s control plane can only be upgraded one minor version at the time,[^1] so increment the version using the `kubernetes_version` variable in the `projects/$CLUSTER_NAME.tfvars` file.

```
kubernetes_version = "1.30.3"  # Increment this
```

Since this variable also defines the k8s versions of the node pools, we will need to pin them until later in the process.
We can do this using the `kubernetes_version` variable in the node pool definitions.

```
node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E4s_v3",
      os_disk_size_gb : 40,
      kubelet_disk_type : "OS",
      min : 1,
      max : 10,
      kubernetes_version : "1.30.3",  # Add this variable set to the current k8s version
    },
  ],
  user : [
    {
      name : "usere8sv5",
      vm_size : "Standard_E8s_v5",
      os_disk_size_gb : 200,
      min : 0,
      max : 100,
      kubernetes_version : "1.30.3",  # Add this variable set to the current k8s version
    },
  ],
}
```

Run a terraform plan and apply.

```bash
tf plan -var-file=projects/$CLUSTER_NAME.tfvars
tf apply -var-file=projects/$CLUSTER_NAME.tfvars
```

#### 4.2 Repeat to upgrade multiple minor versions

If you need to upgrade by multiple minor versions, repeat the previous steps until you have reached the version you require.

### 5. Upgrade node pools

See [](upgrade-cluster:node-upgrade-strategies) for strategies employed for upgrading node pools.

1. First upgrade the *core node pool*. We are forced to use a re-creation strategy here.
1. Then upgrade *user node pools* either with rolling upgrades without using `drain` (preferred), or using re-creation upgrades if they are not running or empty.

Before committing to a node group upgrade its upgrade strategy, overview
currently active nodes:

```bash
kubectl get node --label-columns=alpha.eksctl.io/nodegroup-name
```

#### Upgrading the core node pool (re-creation upgrade)

We are forced to use a re-creation strategy for our core node pool because this is used as the cluster's default node pool (via the [`default_node_pool` config](https://github.com/2i2c-org/infrastructure/blob/HEAD/terraform/azure/cluster.tf#L73-L102)) and only one default node pool can be defined at a time.

Remove the `kubernetes_variable` we added to the core node pool definition in the previous step.

```
node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E4s_v3",
      os_disk_size_gb : 40,
      kubelet_disk_type : "OS",
      min : 1,
      max : 10,
      kubernetes_version : "1.30.3",  # Remove this
    },
  ],
  ...
}
```

Run another terraform plan and apply.
This time, it could take up to 10 mins to complete.

#### Upgrading the user pools (rolling upgrades, using drain or not)

1. *Create a new node group*

   Duplicate the config for the node pool you wish to upgrade.
   Update the name so it doesn't clash, and make sure *not* to copy the `kubernetes_version` variable from the first node pool.

   ```
   node_pools = {
     ...
     user : [
       {
         name : "usere8sv5",
         vm_size : "Standard_E8s_v5",
         os_disk_size_gb : 200,
         min : 0,
         max : 100,
         kubernetes_version : "1.30.3",
       },
       {
         name : "usere8sv5b",  # Change the name
         vm_size : "Standard_E8s_v5",
         os_disk_size_gb : 200,
         min : 0,
         max : 100,
       },
     ],
   }
   ```

   Do the same for any dask node pools defined.

   ```{attention}
   The node pool name must begin with a lowercase letter, contain *only* lowercase letters and numbers, and be between 1 and 12 characters in length.
   ```

   Run a terraform plan and apply to create the new node pool.

1. *Taint and wait*

   If you're not going to forcefully drain the old node pool's nodes (recommended for user node pools), you have to wait for them to empty out before deleting the old node pool.

   First, taint the old node pool's nodes to prevent new pods from scheduling on them.
   It also prevents the cluster-autoscaler from scaling up new such nodes, at least until they have all scaled down.

   ```bash
   kubectl taint node manual-phaseout:NoSchedule -l kubernetes.azure.com/agentpool=usere8sv5
   ```

   Then add a comment in the `.tfvars` file above the old node pool saying:

   ```
   # FIXME: tainted, to be deleted when empty, replaced by equivalent during k8s upgrade
   ```

   You can now commit these changes and come back to the final deletion step at a later point in time.

1. *Delete the old node group*

   If you added a duplicated and renamed node pool, then remove it's definition from the `.tfvars` file.
   Run a terraform plan and apply to delete the node pool.

### 6. Commit changes

During this upgrade, the k8s version and possibly node pool names may have been changed.
Make sure to commit these changes when the upgrade is finished.

## References

[^1]: About Kubernetes' version skew policy: <upgrade-cluster:k8s-version-skew>