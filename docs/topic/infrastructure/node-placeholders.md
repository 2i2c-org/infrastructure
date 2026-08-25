(topic:node-placeholders)=
# Node placeholders

[Earlier](#user-placeholder-warn), we saw that user placeholders do not scale above a single node. This is due to poor scheduling behaviour with respect to the pod disruption.

An alternative approach to reserving capacity on a hub is to use _node_ placeholders. These differ in important ways:

User placeholders
: Ensure that there is new capacity for $N$ users.

Node placeholders
: Ensure that there is total capacity for $M$ nodes.


Node placeholders enable us to ensure that the cluster has $M$ nodes running. However, these are not _new_ nodes — node placeholders ensure that there are $M$ total nodes running in the cluster. If existing users are on the hub, then there will already be several user nodes running and contributing to the total $M$.

## Add Helm configuration
Node placeholders are implemented as a Kubernetes deployment. Each pod is configured with tiny resource requests, and schedules on a dedicated node (that may already exist).

```{code} yaml
:label: placeholder-selector
nodePlaceholder:
  enabled: true
  nodeSelector:
    node.kubernetes.io/instance-type: n2-highmem-4
    # Disable the hub selector
    # 2i2c/hub-name:

  # Control number of nodes required to run
  # Reserves baseline capacity, not surge capacity
  replicas: 0
```

The number of replicas governs how many nodes are required to be running that match the node selector.

:::{note} Choosing a node selector
By default, the placeholder pods will schedule to any _user_ node. Typically we want to reserve capacity for a specific node pool. This can be done by specifying a node selector, as seen in @placeholder-selector.
:::

:::{note} Disabling the hub selector
By default, the node placeholder deployment targets nodes belonging to the current hub. If nodepools are shared across hubs, then the `2i2c/hub-name` selector should be set to `null`.
:::

## Controlling replicas from CI
In GitHub Actions, we have [a workflow](https://github.com/2i2c-org/infrastructure/actions/workflows/scale-placeholders.yaml) for scaling the placeholders of a hub with the appropriate [placeholder configuration](#placeholder-selector). The `Run workflow` button can be used to trigger a CI-driven change to the placeholders of the cluster.

:::{figure} /images/node-placeholder-action.png

Screenshot of the "Scale node placeholders" [workflow](https://github.com/2i2c-org/infrastructure/actions/workflows/scale-placeholders.yaml) GUI in GitHub Actions.
:::
