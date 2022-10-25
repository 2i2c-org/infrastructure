# Manual node administration

The current Kubernetes clusters we run have two types of group nodes ([node pools](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools)), configured to run on: `core` and `user` pools.

The [node selector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector) configuration will ensure the following assignment of pods to nodes:

- **Core and support pods** will be assigned nodes from the core pool
- **User pods** will be assigned to nodes in the user pool.

This separation should protect against user pods exhausting the resources needed by core and support pods.

The machines where the core nodes run, are different than the ones on which the user nodes run.
The type of these machines is chosen based on the number, type, and the resource needs (CPU, memory, etc.) of the pods that will be scheduled to run on these nodes.
Because of this resource dependance, these types might be adjusted in the future.
You can checkout the exact type of the core and user nodes VMs in the `terraform` config for each cloud provider.
For example, here is the [`terraform` config for Google Cloud](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/gcp/variables.tf).

## Freeing up a node

Sometimes you might need to delete or to perform maintenance on a node in the cluster. Some steps need to be performed, in order not to disrupt the pods that run on that node:

1. [Cordon](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#cordon) the node:
    ```bash
    kubectl cordon <node-name>
    ```
    This command will mark the node as `unschedulable` and no new pods will be scheduled to run on this node.

2. Delete *some* of the pods running on the node:
    ```bash
    kubectl delete pods <pod>
    ```

    There are usually three types of pods running on a node, depending on how were they created:
    * Pods created by [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/) objects, through [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

        Once deleted, these Pods will get re-created and assigned to a different node (because the current node it's cordoned).
        The [hub & proxy](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/Chart.yaml) pods are some examples of such pods.
    * Pods created by [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) objects.

        These run on every node, regardless of their `cordon` status. So, they don't need to be deleted, otherwise, they will be re-created on the same cordoned node.
        The [prometheus node-exporter](https://github.com/prometheus-community/helm-charts/blob/main/charts/prometheus-node-exporter/templates/daemonset.yaml) configured [here](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/support/values.yaml#L12), is an example of such a pod.
    * Pods **not** controlled by a Controller

        These are usually the user pods and shouldn't be deleted, as they would disrupt the user. Instead, these will be taken down by the [idle culler](https://github.com/jupyterhub/jupyterhub-idle-culler) when they're in an idle state.

3. Wait for the node to be reclaimed by the [Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler).

   Every 10 seconds, the Cluster Autoscaler checks which nodes are not needed anymore and scales-down the cluster if there are nodes that meet certain conditions. Read more about the scale-down conditions [here](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-does-scale-down-work).
