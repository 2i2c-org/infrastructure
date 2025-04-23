(upgrade-cluster:aws)=

# Upgrade Kubernetes cluster on AWS

## Pre-requisites

1. *Install/upgrade CLI tools*

   Refer to [](new-cluster:prerequisites) on how to do this.

   ```{important}
   Ensure you have the latest version of `eksctl`, it matters.
   ```

2. *Learn/recall how to generate an `eksctl` config file*

   When upgrading an EKS cluster, we will use `eksctl` extensively and reference
   a generated config file, `$CLUSTER_NAME.eksctl.yaml`. It's generated from the
   the `$CLUSTER_NAME.jsonnet` file.

   ```bash
   # re-generate an eksctl config file for use with eksctl
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   ```

## Cluster upgrade

### 1. Prepare two terminal sessions

Start two terminal sessions and set `CLUSTER_NAME=...` in both.

In the first terminal, setup your AWS credentials ([according to this
documentation](cloud-access:aws)) and change you working directory to the
`eksctl` folder.

In the second terminal, setup k8s credentials with `deployer
use-cluster-credentials $CLUSTER_NAME`.

```{note}
If you would use `deployer use-cluster-credentials` where you have setup your
AWS credentials, you would no longer act as your your AWS user but the
`hub-deployer-user` that doesn't have the relevant permissions to work with
`eksctl`.
```

### 2. Check cluster status and activity

Before upgrading, get a sense of the current status of the cluster and users
activity in it.

```bash
# get nodes, and k8s version, and their node group names
# - what node groups are active currently?
kubectl get node --label-columns=alpha.eksctl.io/nodegroup-name

# get all pods
# - are there any non-running/non-ready pod with issues before upgrading?
kubectl get pod -A

# get users' server and dask cluster pods
# - how many user servers are currently running?
# - is this an acceptable time to upgrade?
kubectl get pod -A -l "component=singleuser-server"
kubectl get pod -A -l "app.kubernetes.io/component in (dask-scheduler, dask-worker)"
```

### 3. Notify in slack

Notify others in 2i2c that your are starting this cluster upgrade in the
`#maintenance-notices` Slack channel.

### 4. Upgrade the k8s control plane[^2]

#### 4.1. Upgrade the k8s control plane one minor version

The k8s control plane can only be upgraded one minor version at the time,[^1] so
increment the version field in the `.jsonnet` file.

```yaml
{
   name: "openscapeshub",
   region: clusterRegion,
   version: "1.29", # increment this
}
```

Re-generate the `.yaml` file, and then perform the upgrade which typically takes
~10 minutes. This upgrade is not expected to be disruptive for EKS clusters as
they come with multiple replicas of the k8s api-server.

```bash
jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
eksctl upgrade cluster --config-file=$CLUSTER_NAME.eksctl.yaml --approve
```

```{note}
If you see the error `Error: the server has asked for the client to provide
credentials` don't worry, if you try it again you will find that the cluster is
now upgraded.
```

#### 4.2. Upgrade EKS add-ons

As documented in `eksctl`'s documentation[^2], we also need to upgrade EKS
add-ons. This upgrade is believed to very briefly disrupt networking.

```bash
# upgrade all EKS addons (takes up to a few minutes)
eksctl update addon --config-file=$CLUSTER_NAME.eksctl.yaml
```

```{note}
Since November 2024, the add-ons are systematically installed as EKS managed
add-ons and not self-managed as they were before when `eksctl` installed them
without involving EKS.
```

#### 4.3. Repeat to upgrade multiple minor versions

If you need to upgrade multiple minor versions, repeat the previous steps
starting with the minor version upgrade.

(upgrade-cluster:aws:node-groups)=

### 5. Upgrade node groups

All of the cluster's node groups should be upgraded. Strategies to upgrade nodes
are introduced in [](upgrade-cluster:node-upgrade-strategies).

1. First upgrade *the core node group* with a rolling upgrade using `drain`.
2. Then upgrade *user node group(s)* with rolling upgrades without using
   `drain`, or using re-creation upgrades if they aren't running or empty.

Before committing to a node group upgrade its upgrade strategy, overview
currently active nodes:

```bash
kubectl get node --label-columns=alpha.eksctl.io/nodegroup-name
```

#### Performing rolling upgrades (using drain or not)

1. *Create a new node group*

   If you are going to use drain (core node groups), rename the node group you
   want to do a rolling upgrade on in the `.jsonnet` file, for example by
   adjusting a `nameSuffix` from `a` to `b`. If you aren't going to use drain
   (user node groups), add a duplicate but renamed entry instead.

   Node group names are set by `namePrefix`, `nameSuffix`, and
   `nameIncludeInstanceType`. Example node group names are `core-b`,
   `nb-r5-xlarge`, `nb-r5-xlarge-b`, `dask-r5-4xlarge`.

   ```bash
   # create a new node group (takes ~5 min)
   # IMPORTANT: review the --include flag's value

   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="core-b"
   ```

2. *Optionally taint and wait*

   If you aren't going to forcefully drain the old node group's nodes, you have
   to wait for the nodes to empty out before deleting the old node group.

   First taint the old node group's nodes to stop new pods from scheduling on
   them. Doing this also prevents the cluster-autoscaler from scaling up new
   such nodes, at least until they have all scaled down.

   ```bash
   kubectl taint node manual-phaseout:NoSchedule -l alpha.eksctl.io/nodegroup-name=core-b
   ```

   Then a comment in the `.jsonnet` file above to the old node group saying:

   ```json
   // FIXME: tainted, to be deleted when empty, replaced by equivalent during k8s upgrade
   ```

   You can now commit changes and come back to the final deletion step at a
   later point in time.

3. *Delete the old node group*

   ````{important}
   Before draining and deleting the old node group, you need to update the `tigera-operator`
   deployment and force it to not use the old node group anymore.
   Otherwise, the the drain process will get stuck.

   This is because `tigera-operator` tolerates all taints by default including
   `NoSchedule`, and it will recreate itself indefinitely on the tainted node
   that's being drained even though it's tainted with `NoSchedule`.

   To fix this, you need to edit the `tigera-operator` deployment with:

   ```bash
   kubectl edit deployment tigera-operator -n tigera-operator
   ```

   and search after `Exists` and remove the following toleration from that entry:

   ```yaml
   tolerations:
     - effect: NoSchedule
       operator: Exists
   ```
   You can now proceed with the drain and delete process.
   ````

   If you added a duplicate renamed node group, then first remove the old node
   group in the `.jsonnet` file.

   ```bash
   # drains and deletes node groups not found in config (takes ~20s if the node groups has no running nodes)
   # IMPORTANT: note that --approve is needed and commented out

   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   eksctl delete nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --only-missing # --approve
   ```

   ```{note}
   The `eksctl` managed drain operation may get stuck but you could help it along
   by finding the pods that fail to terminate with `kubectl get pod -A`, and then
   manually forcefully terminating them with `kubectl delete pod --force <...>`.
   ```

#### Performing re-creation upgrades

If you do maintenance on a cluster with no running user workloads (user servers,
dask gateway workers), a quick and simple strategy is to delete all user node
groups and then re-create them. The `eksctl [delete|create] nodegroup` commands
can work with multiple node group at the time by using wildcards in the
`--include` flag.

1. *Delete node group(s)*

   ```bash
   # delete the node groups (takes ~20s if the node groups has no running nodes)
   # IMPORTANT: review the --include flag's value
   # IMPORTANT: note that --approve is needed and commented out

   eksctl delete nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="nb-*,dask-*" # --approve
   ```

2. *Wait ~60 seconds*

   If we don't wait now, our create command may fail without an error and
   instead log a message like _# existing nodegroup(s) (...) will be excluded_.
   If it happens though, you can just re-run the create command though.

3. *Re-create node group(s)*

   ```bash
   # re-create node group(s) (takes ~5 min)
   # IMPORTANT: review the --include flag's value

   eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="nb-*,dask-*"
   ```

### 6. Notify in slack

Notify others in 2i2c that you've finalized the cluster upgrade in the
`#maintenance-notices` Slack channel.

### 7. Commit changes

During this upgrade, the k8s version and possibly the node group name might have
been changed. Make sure you commit this changes after the upgrade is finished.

## References

[^1]: About Kubernetes' version skew policy: <upgrade-cluster:k8s-version-skew>
[^2]: `eksctl`'s cluster upgrade documentation: <https://eksctl.io/usage/cluster-upgrade/>
