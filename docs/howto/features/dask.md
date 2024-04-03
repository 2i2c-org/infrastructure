(howto:features:daskhubs)=
# Add support for daskhubs in an existing cluster

## GCP

Setting up dask nodepools with terraform can be done by adding the following to the cluster's terraform config file:

```terraform
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

1. In the appropriate `.jsonnet` file, add a `dask_nodes` definition 
   add a node definition for the appropriate GPU node type:

   ```
    dask_nodes = {
    #  A not yet fully established policy is being developed about using a single
    #  node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
      "n2-highmem-16" : {
        min : 0,
        max : 200,
        machine_type : "n2-highmem-16",
      },
    }
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
