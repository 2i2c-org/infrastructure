# Setup a dedicated nodepool for a hub on a shared cluster

Some hubs on shared clusters require dedicated nodepools, for a few reasons:

1. Helpful to pre-warm during events, as we can scale a single nodepool up/down
   without worrying about effects from other hubs on the same cluster.
2. (In the future) Helpful with cost isolation, as we can track how much a
   nodepool is costing us.

## GCP

1. Setup a new nodepool in terraform, via the `<cluster-name>.tfvars` for the
   cluster. Add the new nodepool to `notebook_nodes`:

   ```terraform
   notebook_nodes = {
     "<community-name>": {
         min: 0,
         max: 100,
         machine_type: "<machine-type>",
         labels: {
            "2i2c.org/community": "<community-name>"
         },
         taints: [{
            key: "2i2c.org/community",
            value: "<community-name>",
            effect: "NO_SCHEDULE"
         }],
         gpu: {
            enabled: false,
            type: "",
            count: 0
         },
         resource_labels: {
            "community": "<community-name>"
         }
      }
   }
   ```

   This sets up a new node with:

   1. Kubernetes labels so we can tell the scheduler that user pods of this hub
      should come to this nodepool.
   2. Kubernetes taints so user pods of *other* hubs will not be scheduled on this
      nodepool.
   3. GCP Resource Labels (unrelated to Kubernetes Labels!) that help us track costs.
      The key name here is different from (1) and (2) because it must start with a
      letter, and can not contain `/`.

   Once done, run `terraform apply` appropriately to bring this nodepool up.

2. Configure the hub's helm values to use this nodepool, and this nodepool only.

   ```yaml
   jupyterhub:
      singleuser:
         nodeSelector:
            2i2c.org/community: <community-name>
         extraTolerations:
            - key: "2i2c.org/community"
              operator: "Equal"
              value: "<community-name>"
              effect: "NoSchedule"
   ```

   ```{note}
   If this is a `daskhub`, nest these under a `basehub` key.
   ```

   This tells JupyterHub to place user pods from this hub on the nodepool we had
   just created!
   
## Node type and minimum nodepool size considerations

When setting up a dedicated node pool for a hub, particularly a hub supporting
an *event*, it's important to consider the node type and minimum node size
used. As there will likely only be minimal number of users until the event
starts, it's helpful to set the *minimum node pool size* to 0 until at least
*a week* before the start of the event. A smaller node type is also advised
until a week before the event.
