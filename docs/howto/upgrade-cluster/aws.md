(upgrade-cluster:aws)=

# Upgrade Kubernetes cluster on AWS

```{warning}
This upgrade will cause disruptions for users and trigger alerts for
[](uptime-checks). To help other engineers, communicate that your are starting a
cluster upgrade in the `#maintenance-notices` Slack channel.
```

```{warning}
We haven't yet established a policy for planning and communicating maintenance
procedures to users. So preliminary, only make a k8s cluster upgrade while the
cluster is unused or that the maintenance is communicated ahead of time.
```

## Pre-requisites

1. *Install or upgrade CLI tools*

   Install required tools as documented in [](new-cluster:aws-required-tools),
   and ensure you have a recent version of eksctl.

2. *Consider changes to `template.jsonnet`*

   The eksctl config jinja2 template `eksctl/template.jsonnet` was once used to
   generate the jsonnet template `eksctl/$CLUSTER_NAME.jsonnet`, that has been
   used to generate an actual eksctl config.

   Before upgrading an EKS cluster, it could be a good time to consider changes
   to `eksctl/template.jsonnet` since this cluster's jsonnet template was last
   generated, which it was initially according to
   [](new-cluster:aws:generate-cluster-files).

   To do this first ensure `git status` reports no changes, then generate new
   cluster files using the deployer script, then restore changes to everything
   but the `eksctl/$CLUSTER_NAME.jsonnet` file.

   ```bash
   export CLUSTER_NAME=<cluster-name>
   export CLUSTER_REGION=<cluster-region-like ca-central-1>
   export HUB_TYPE=<hub-type-like-basehub>
   ```

   ```bash
   # only continue below if git status reports a clean state
   git status

   # generates a few new files
   deployer generate-aws-cluster --cluster-name=$CLUSTER_NAME --cluster-region=$CLUSTER_REGION --hub-type=$HUB_TYPE

   # overview changed files
   git status

   # restore changes to all files but the .jsonnet files
   git add *.jsonnet
   git checkout ..  # .. should be the git repo's root
   git reset

   # inspect changes
   git diff
   ```

   Finally if you identify changes you think should be retained, add and commit
   them. Discard the remaining changes with a `git checkout .` command.

3. *Learn how to generate an `eksctl` config file*

   When upgrading an EKS cluster, we will use `eksctl` extensively and reference
   a generated config file, `$CLUSTER_NAME.eksctl.yaml`. It's generated from the
   the `$CLUTER_NAME.jsonnet` file.

   If you update the .jsonnet file, make sure to re-generate the .yaml file
   before using `eksctl`. Respectively if you update the .yaml file directly,
   remember to update the .jsonnet file.

   ```bash
   # re-generate an eksctl config file for use with eksctl
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   ```

## Cluster upgrade

1. *Ensure in-cluster permissions*

   The k8s api-server won't accept commands from you unless you have configured
   a mapping between the AWS user to a k8s user, and `eksctl` needs to make some
   commands behind the scenes.

   This mapping is done from a ConfigMap in kube-system called `aws-auth`, and
   we can use an `eksctl` command to influence it.

   ```bash
   eksctl create iamidentitymapping \
      --cluster=$CLUSTER_NAME \
      --region=$CLUSTER_REGION \
      --arn=arn:aws:iam::<aws-account-id>:user/<iam-user-name> \
      --username=<iam-user-name> \
      --group=system:masters
   ```

2. *Acquire and configure AWS credentials*

   Visit https://2i2c.awsapps.com/start#/ and acquire CLI credentials.

   In case the AWS account isn't managed there, inspect
   `config/$CLUSTER_NAME/cluster.yaml` to understand what AWS account number to
   login to at https://console.aws.amazon.com/.

   Configure credentials like:

   ```bash
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   ```

3. *Upgrade the k8s control plane's one minor version*

   The k8s control plane can only be upgraded one minor version at the time.[^1]
   So, update the eksctl config's version field one minor version.

   Then, perform the upgrade which typically takes ~10 minutes.

   ```bash
   eksctl upgrade cluster --config-file=$CLUSTER_NAME.eksctl.yaml --approve
   ```

   ```{note}
   If you see the error `Error: the server has asked for the client to provide credentials` don't worry, if you try it again you will find that the cluster is now upgraded.
   ```

4. *Upgrade node groups up to two minor versions above the k8s control plane*

   A node's k8s software (`kubelet`) can be up to two minor versions ahead or
   behind the control plane version.[^1] Due to this, you can plan your cluster
   upgrade to only involve one node group upgrade even if you increment the
   control plane four minor versions.

   So if you upgrade from k8s 1.21 to 1.24, you can for example upgrade the k8s
   control plane from 1.21 to 1.22, then upgrade the node groups from 1.21 to
   1.24, followed by upgrading the control plane two steps in a row.

   To upgrade (unmanaged) node groups, you delete them and then them back. When
   adding them back, make sure your cluster config's k8s version is what you
   want the node groups to be added back as.

   1. Update the k8s version in the config temporarily

      This is to influence the k8s software version for the nodegroup's we
      create only. We can choose something two minor versions of the current k8s
      control plane version.

   2. Add a new core node group (like `core-b`)

      Rename (part 1/3) the config file's entry for the core node group
      temporarily when running this command, either from `core-a` to `core-b` or
      the other way around.

      ```bash
      eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="core-b"
      ```

   3. Delete all old node groups (like `core-a,nb-*,dask-*`)

      Rename (part 2/3) the core node group again in the config to its previous
      name, so the old node group can be deleted with the following command.

      ```bash
      eksctl delete nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="core-b,nb-*,dask-*" --approve --drain=false
      ```

      Rename (part 3/3) the core node group one final time in the config to its
      new name, as that represents the state of the EKS cluster.

   4. Re-create all non-core node groups (like `nb-*,dask-*`)

      ```bash
      eksctl create nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml --include="nb-*,dask-*"
      ```

   5. Restore the k8s version in the config

      We adjusted the k8s version in the config to influence the desired version
      of our created nodegroups. Let's restore it to what the k8s control plane
      currently have.

5. *Upgrad EKS add-ons (takes ~3*5s)*

   As documented in `eksctl`'s documentation[^1], we also need to upgrade three
   EKS add-ons enabled by default.

   ```bash
   # upgrade the kube-proxy daemonset
   eksctl utils update-kube-proxy --config-file=$CLUSTER_NAME.eksctl.yaml --approve

   # upgrade the aws-node daemonset
   eksctl utils update-aws-node --config-file=$CLUSTER_NAME.eksctl.yaml --approve
   kubectl patch daemonset -n kube-system aws-node --patch='{"spec":{"template":{"spec":{"$setElementOrder/containers":[{"name":"aws-node"}],"containers":[{"name":"aws-node","securityContext":{"allowPrivilegeEscalation":null,"runAsNonRoot":null}}]}}}}'

   # upgrade the coredns deployment
   eksctl utils update-coredns --config-file=$CLUSTER_NAME.eksctl.yaml --approve
   ```

   ```{note} Ignore these failures
   You may find that the aws-node daemonset's pods fail to start because of a
   too restrictive container securityContext not running as root.

   This is https://github.com/weaveworks/eksctl/issues/6048 and can be resolved
   by removing `runAsNonRoot: true` and `allowPrivilegeEscalation: false`. Using
   `kubectl edit daemonset aws-node --output-patch=true` led to the `kubectl
   patch` snippet we use above.

   The kube-proxy deamonset's pods may fail to pull the image, but its an issue
   that goes away when upgrading to or beyond k8s 1.23.
   ```

6. *Repeat steps 3 and 5 if needed*

   If you upgrade k8s multiple minor versions, repeat step 3 and 5, where you
   increment it one minor version at the time.

## References

[^1]: `eksctl`'s cluster upgrade documentation: <https://eksctl.io/usage/cluster-upgrade/>
