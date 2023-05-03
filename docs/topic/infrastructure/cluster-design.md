# Cluster design considerations

## Core nodes' instance type

Each cluster is setup with a *core node pool*. Its expected to be static in size
and always running. The core node's instance types should have: allocatable CPU,
allocatable Memory, and allowed Pods per node, to efficiently schedule and
reliably run:

1. Kubernetes system pods - network policy enforcement, cluster
   autoscaler, kube-dns, etc.

2. Per-cluster support pods - like prometheus, grafana, cert-manager, etc.

3. JupyterHub core pods - like hub, proxy, user-scheduler, etc

4. (Optional) DaskGatway core pods - like gateway, controller, proxy.

Since the core nodes are *always running*, they form a big chunk of the
cluster's *base cost* - the amount of money it costs each day, regardless of
current number of running users. Picking an appropriate instance type for the
core nodes has a big effect.

### CPU and Memory

Kubernetes system Pods on GKE, EKS, and AKS will require different amount of
allocatable capacity, and it can differ if we enable various features such as
network policy enforcement.

Typically we run out of allocatable Memory faster than CPU, which makes us
benefit from nodes with a high memory to CPU ratio, such as the `n2-highmem`
nodes on GCP or `r5` nodes on AWS.

### Allocatable pods per node

Node's of different types can only schedule so many pods on them.

- GKE instance types supports 110 pods per node and typically won't have issues
  with this, unless perhaps in a shared k8s cluster with many JupyterHub
  installations.
- EKS instance types support varying amounts of pods per node, and the smallest
  nodes with two CPU cores typically only allows for 27 pods per node.

### System pods anti-affinity

Pods may be required to run on separate nodes. This has caused multiple nodes be
required on GKE clusters that has `calico-typha` pods from the network policy
enforcement.

The `calico-typha` pods vary in amount, from only one to a few, depending on the
number of nodes in the k8s cluster thanks to a HorizontalPodAutoscaler (HPA).
The HPA can be re-configured via a k8s ConfigMap.

```yaml
# Below is a snippet from the ConfigMap calico-typha-horizontal-autoscaler in a
# GKE cluster with network policy enforcement enabled. It can be edited, and
# changes to it will be respected across k8s upgrades it seems.
data:
  ladder: |-
    {
      "coresToReplicas": [],
      "nodesToReplicas":
      [
        [1, 1],
        [2, 2],
        [100, 3],
        [250, 4],
        [500, 5],
        [1000, 6],
        [1500, 7],
        [2000, 8]
      ]
    }
```

On GKE clusters with network policy enforcement, we look to edit the
`calico-typha-horizontal-autoscaler` ConfigMap in `kube-system` to avoid scaling
up to two replicas unless there are very many nodes in the k8s cluster.

### Our instance type choice

We default to setting up new k8s clusters's core node pool with instance types
of either 2 CPU and 16GB of memory or 4 CPU and 32GB of memory.

On GKE we setup `n2-highmem-2` nodes for new basehub installations and
`n2-highmem-4` for new daskhub installations. A risk of using `n2-highmem-2` is
that `prometheus-server` may require more memory than is available.

On EKS we always use the `r5.xlarge` nodes to avoid running low on allocatable
pods.

## Network Policy

When hubs belonging to multiple organizations are run on the same cluster,
we **must** enable [NetworkPolicy enforcement](https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy)
to isolate them from each other.

## Cloud access credentials for hub users

For hub users to access cloud resources (like storage buckets), they will need
to be authorized via a [GCP ServiceAccount](https://cloud.google.com/iam/docs/service-accounts).
This is different from a [Kubernetes ServiceAccount](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/),
which is used to authenticate and authorize access to kubernetes resources (like spawning pods).

For dask hubs, we want to provide users with write access to at least one storage
bucket they can use for temporary data storage. User pods need to be given access to
a GCP ServiceAccount that has write permissions to this bucket. There are two ways
to do this:

1. Provide appropriate permissions to the GCP ServiceAccount used by the node the user
   pods are running on. When used with [Metadata Concealment](https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata#overview),
   user pods can read / write from storage buckets. However, this grants the same permissions
   to *all* pods on the cluster, and hence is unsuitable for clusters with multiple
   hubs running for different organizations.

2. Use the [GKE Cloud Config Connector](https://cloud.google.com/config-connector/docs/overview) to
   create a GCP ServiceAccount + Storage Bucket for each hub via helm. This requires using
   [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity) and
   is incompatible with (1). This is required for multi-tenant clusters, since users on a hub
   have much tighter scoped permissions.

Long-term, (2) is the appropriate way to do this for everyone. However, it affects the size
of the core node pool, since it runs some components in the cluster. For now, we use (1) for
single-tenant clusters, and (2) for multi-tenant clusters. If nobody wants a scratch GCS bucket,
neither option is required.
