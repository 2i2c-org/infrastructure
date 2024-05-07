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

3. *Two terminal sessions*

   Use one terminal session/tab to run `eksctl` commands and where you later
   configure your AWS credentials, and another to run `kubectl` commands where
   you setup easily with `deployer use-cluster-credentials $CLUSTER_NAME`.

   Declare `CLUTER_NAME=...` in both terminals, and put yourself in the `eksctl`
   folder in the one to run `eksctl` commands. This allows you to identify the
   terminal session among many if you upgrade multiple clusters at the same
   time.

   The motivation for two terminal sessions are:

   1. If you would use `deployer use-cluster-credentials` in a terminal where
      you configured your personal AWS credentials, you will no longer act as
      your AWS user but the `hub-deployer-user` that doesn't have the relevant
      permissions to work with `eksctl`.
   2. If you would use `eksctl utils write-kubeconfig` instead to setup your AWS
      user's credentials with `kubectl` in a single terminal, you wouldn't be
      able to use `kubectl` while `eksctl` was working.

## Cluster upgrade

### 1. Acquire and configure AWS credentials

Refer to [](cloud-access:aws) on how to do this.

### 2. Ensure in-cluster permissions

`eksctl` may need to use your AWS credentials to act within the k8s cluster
(`kubectl drain` during node pool operations for example), but the k8s
api-server won't accept commands from your AWS user unless you have configured a
mapping between it to a k8s user.

This mapping is done from a ConfigMap in kube-system called `aws-auth`, and we
should use an `eksctl` command to influence it.

```bash
eksctl create iamidentitymapping \
   --cluster=$CLUSTER_NAME \
   --region=$CLUSTER_REGION \
   --arn=arn:aws:iam::<aws-account-id>:user/<iam-user-name> \
   --username=<iam-user-name> \
   --group=system:masters
```

### 3. Communicate

Communicate that your are starting a cluster upgrade in the
`#maintenance-notices` Slack channel.

### 4. Upgrade the k8s control plane

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

As documented in `eksctl`'s documentation[^1], we also need to upgrade three EKS
add-ons managed by `eksctl` (by EKS these are considered self-managed add-ons),
and one declared in our config (by EKS this is considered a managed add-on).

These upgrades are believed to briefly disrupt networking.

```bash
# upgrade the kube-proxy daemonset (takes ~5s)
eksctl utils update-kube-proxy --config-file=$CLUSTER_NAME.eksctl.yaml --approve

# upgrade the aws-node daemonset (takes ~5s)
eksctl utils update-aws-node --config-file=$CLUSTER_NAME.eksctl.yaml --approve

# upgrade the coredns deployment (takes ~5s)
eksctl utils update-coredns --config-file=$CLUSTER_NAME.eksctl.yaml --approve

# upgrade the aws-ebs-csi-driver addon's deployment and daemonset (takes ~60s)
eksctl update addon --config-file=$CLUSTER_NAME.eksctl.yaml
```

#### 4.3. Repeat to upgrade multiple minor versions

If you need to upgrade multiple minor versions, repeat the previous steps
starting with the minor version upgrade.

### 5. Upgrade node groups

All of the cluster's node groups should be upgraded. Strategies to upgrade nodes
are introduced in [](upgrade-cluster:node-upgrade-strategies).

1. Upgrade *the core node group* with a rolling upgrade using `drain`.
2. Upgrade *user node group(s)* with rolling upgrades without using `drain`, or
   optionally using re-creation upgrades.

#### Performing rolling upgrades (with or without drain)

1. Add a new node group

   Add a new node group in the `.jsonnet` file. Name it `core-b` or similar if
   the other was named `core-a`, or the other way around.

   ```bash
   # create a new nodegroup (takes ~5 min)
   # IMPORTANT: review the --include flag's value
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="core-b"
   ```

   ```{important}
   The `eksctl create nodegroup` can fail quietly when re-creating a node group
   that has been deleted recently (last ~60 seconds). If you see messages like
   _# existing nodegroup(s) (...) will be excluded_ and _created 0
   nodegroup(s)_, you can just re-run the `create` command.
   ```

2. Taint the old node group's nodes

   This makes new pods not able to schedule on any of these nodes, and the
   cluster-autoscaler will guess that it shouldn't try to start up nodes from
   this node group.

   ```bash
   kubectl taint node manual-phaseout:NoSchedule -l alpha.eksctl.io/nodegroup-name=core-b
   ```

3. Optionally wait for old nodes' pods to go away

   If you aren't going to forcefully drain the old node group's nodes, you have
   to wait before deleting the old node group. If you do, add a comment in the
   `.jsonnet` file next to the old node group saying:

   ```json
   // FIXME: tainted, to be deleted when empty, replaced by equivalent during k8s upgrade
   ```

4. Remove the old node group

   Remove the old node group in the `.jsonnet` file.

   ```bash
   # drain and delete all non-listed nodegroups (takes ~20s if the node groups has no running nodes)
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   eksctl delete nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --approve --drain=true --only-missing
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

1. Delete node group(s)

   ```bash
   # drain nodes and delete the nodegroups (takes ~20s if the node groups has no running nodes)
   # IMPORTANT: review the --include flag's value
   eksctl delete nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --approve --drain=true --include="nb-*,dask-*"
   ```

2. Re-create node group(s)

   ```bash
   # create a new nodegroup (takes ~5 min)
   # IMPORTANT: review the --include flag's value
   eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="nb-*,dask-*"
   ```

### 5. Commit changes

During this upgrade, the k8s version and possibly the node group name might have
been changed. Make sure you commit this changes after the upgrade is finished.

## References

[^1]: About Kubernetes' version skew policy: <upgrade-cluster:k8s-version-skew>
[^2]: `eksctl`'s cluster upgrade documentation: <https://eksctl.io/usage/cluster-upgrade/>
