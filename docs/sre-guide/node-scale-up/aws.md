(scaling-nodepools:aws)=
# AWS

`eksctl` creates nodepools that are mostly immutable, except for autoscaling properties -
minimum and maximum number of nodes. In certain cases, it might be helpful to 'scale up'
a nodegroup in a cluster before an event, to test cloud provider quotas or to make user
server startup faster.

1. Open the appropriate `.jsonnet` file for the cluster in question (located in the `eksctl` folder).
   Depending on how you intend to scale the nodepools, there are two approaches you may take.

   1. **Scale all nodepools.**
      To scale all nodepools, locate the `minSize` property of the `nb` node group and change the value to what you want.
      An example can be found here:
      <https://github.com/2i2c-org/infrastructure/blob/f40cfbc2b5bd236a1f95e406a6f6d9bec99e55d2/eksctl/2i2c-aws-us.jsonnet#L102>
   
   2. **Scale a specific nodepool.**
      If you only wish to scale a specific nodepool, you can add the `minSize` property to the local `notebookNodes` variable next to the `instanceType` that you wish to scale.
      An example can be found here:
      <https://github.com/2i2c-org/infrastructure/blob/f40cfbc2b5bd236a1f95e406a6f6d9bec99e55d2/eksctl/carbonplan.jsonnet#L40>

   ```{warning}
   It is currently unclear if *lowering* the `minSize` property just allows
   the autoscaler to reclaim nodes, or if it actively destroys nodes at time
   of application! If it actively destroys nodes, it is unclear if it does
   so regardless of user pods running in these nodes! Until this can be
   determined, please do scale-downs only when there are no users on
   the nodes.
   ```

2. Render the `.jsonnet` file into a YAML file with:
   ```bash
   export CLUSTER_NAME=<your_cluster>
   ```

   ```bash
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   ```

3. Use `eksctl` to scale the cluster.

   ```bash
   eksctl scale nodegroup --config-file=$CLUSTER_NAME.eksctl.yaml
   ```

   ```{note}
   `eksctl` might print warning messages such as
   `retryable error (Throttling: Rate exceeded`. This is just a warning,
   and shouldn't have any actual effects on the scaling operation except
   cause a delay.
   ```

4. Validate that appropriate new nodes are coming up by authenticating
   to the cluster, and running `kubectl get node`.

5. Commit the change and make a PR, and note that you have already
   completed the scaling operation. This is flexible, as the scaling operation
   might need to be timed differently in each case. The goal is to make sure
   that the `minSize` parameter in the github repository matches reality.
