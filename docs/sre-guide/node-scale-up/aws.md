(scaling-nodepools:aws)=
# AWS

`eksctl` creates nodepools that are mostly immutable, except for autoscaling properties -
minimum and maximum number of nodes. In certain cases, it might be helpful to 'scale up'
a nodegroup in a cluster before an event, to test cloud provider quotas or to make user
server startup faster.

1. Open the appropriate `.jsonnet` file for the cluster in question (located in the `eksctl` folder).
   Depending on how you intend to scale the nodepools, there are two approaches you may take.

1. Scale the desired nodepool

Depending on which nodepool(s) you want to scale up, tweak the arguments of `cluster.withNodeGroupConfigOverride` to match your needs.
   ```json
   cluster.withNodeGroupConfigOverride(
      c,
      kind='notebook',
      instanceType='r5.4xlarge',
      hubName='prod',
      overrides={
         desiredCapacity: 10,
         minSize: 10,
      }
   )
   ```
   Where:
   - `c` is the cluster object created with `cluster.makeCluster` defined in `eksctl/libsonnet/cluster.jsonnet`
   - both `minSize` and `desiredCapacity` represent the number of nodes wanted in the nodepool

   ````{tip}
   You can also chain multiple `cluster.withNodeGroupConfigOverride` for better matching of nodepools to scale.
   ```json
   cluster.withNodeGroupConfigOverride(
      cluster.withNodeGroupConfigOverride(
         c,
         kind='notebook',
         instanceType='r5.4xlarge',
         hubName='pythia-binder',
         overrides={
            desiredCapacity: 11,
            minSize: 11,
         }
      ),
      kind='notebook',
      instanceType='r5.4xlarge',
      hubName='prod',
      overrides={
         desiredCapacity: 11,
         minSize: 11,
      }
   )
   ```
   ````

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
