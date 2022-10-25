(scaling-nodepools:aws)=
# AWS

`eksctl` creates nodepools that are mostly immutable, except for autoscaling properties -
minimum and maximum number of nodes. In certain cases, it might be helpful to 'scale up'
a nodegroup in a cluster before an event, to test cloud provider quotas or to make user
server startup faster.

1. Open the appropriate `.jsonnet` file for the cluster in question (located in the `eksctl` folder), and set a
   `minSize` property of `notebookNodes` to the appropriate number you want.

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
   jsonnet <your-cluster>.jsonnet > <your-cluster>.eksctl.yaml
   ```

3. Use `eksctl` to scale the cluster.

   ```bash
   eksctl scale nodegroup --config-file=<your-cluster>.eksctl.yaml
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
