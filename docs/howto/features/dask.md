# Add support for daskhubs

(howto:features:daskhub:existing-hub)=
## To an existing hub

A daskhub setup can now also be enabled **after** a hub has been setup as a basehub.

To enable dask-gateway support on a hub, the following configuration changes need to be made to the hub's values file:

1. set `dask-gateway.enabled` to true:

    ```yaml
    dask-gateway:
      enabled: true
    ```

1. set `jupyterhub.custom.daskGateway.enabled` to true:

    ```yaml
    jupyterhub:
      custom:
        daskhubSetup:
          enabled: true
    ```

1. set `jupyterhub.singleuser.cloudMetadata.blockWithIptables` to false:

    This is to don't block access to the cloud provider's metadata server!
    If we do the coupling between the cloud providers IAM permissions and
    the credentials provided to pod's by mounting a k8s ServiceAccount
    with certain annotations on breaks (AWS IRSA, GCP workload identity).
    This in turn results in users unable to able to access AWS/GCP object
    storage buckets.

    ```yaml
    jupyterhub:
      singleuser:
        cloudMetadata:
          blockWithIptables: false
    ```

1. if binderhub is enabled to work against a private container registry:

    Then dask-gateway's scheduler and worker pods need to pull from that
    registry, so follow steps in [](features:binderhub-service:private-registry)
    to set up permissions for that.

(howto:features:daskhub)=
## To an existing cluster

## GCP

Setting up dask nodepools with terraform can be done by adding the following to the cluster's terraform config file:

```
# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
}
```

This provisions a single `n2-highmem-16` nodepool. The reasons behind the choice of machine can be found in https://github.com/2i2c-org/infrastructure/issues/2687.

````{tip}
Don't forget to run terraform plan and terraform apply for the new node pool to get created.
```bash
terraform plan -var-file projects/$CLUSTER_NAME.tfvars
```
```bash
terraform apply -var-file projects/$CLUSTER_NAME.tfvars
```
````

### AWS

We use `eksctl` with `jsonnet` to provision our kubernetes clusters on
AWS, and we can configure a node group there for the dask pods to run onto.

1. In the appropriate `.jsonnet` file, update the `local daskNodes`:

    This is how it could look in a .jsonnet file after updating the local daskNodes = [] variable:

    ```
    local daskNodes = [
        // Node definitions for dask worker nodes. Config here is merged
        // with our dask worker node definition, which uses spot instances.
        // A `node.kubernetes.io/instance-type label is set to the name of the
        // *first* item in instanceDistribution.instanceTypes, to match
        // what we do with notebook nodes. Pods can request a particular
        // kind of node with a nodeSelector
        //
        // A not yet fully established policy is being developed about using a single
        // node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
        //
        { instancesDistribution+: { instanceTypes: ["r5.4xlarge"] }},
    ];
    ```

2. Render the `.jsonnet` file into a `.yaml` file that `eksctl` can use

   ```bash
   export CLUSTER_NAME=<your_cluster>
   ```

   ```bash
   jsonnet $CLUSTER_NAME.jsonnet > $CLUSTER_NAME.eksctl.yaml
   ```

3. Create the nodegroup

   ```bash
   eksctl create nodegroup -f $CLUSTER_NAME.eksctl.yaml
   ```

   This should create the nodegroup with 0 nodes in it, and the
   autoscaler should recognize this! `eksctl` will also setup the
   appropriate driver installer, so you won't have to.
