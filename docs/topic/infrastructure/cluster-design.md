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

(topic:cluster-design:instance-type)=
### Our instance type choice

#### For nodes where core services will be scheduled on

```{note}
In the 2i2c infrastructure, these node groups always have the word "core" in their name.
```

We default to setting up new k8s clusters's core node pool with instance types
of either 2 CPU and 16GB of memory or 4 CPU and 32GB of memory.

On GKE we setup `n2-highmem-2` nodes for new basehub installations and
`n2-highmem-4` for new daskhub installations. A risk of using `n2-highmem-2` is
that `prometheus-server` may require more memory than is available.

On EKS we always use the `r5.xlarge` nodes to avoid running low on allocatable
pods.

#### For nodes where user servers will be scheduled on

```{note}
In the 2i2c infrastructure, these nodes are grouped under slightly different names, depending on the cloud provider, but they all refer to the group of nodes where user servers will be scheduled on. They are called:

- "notebook" node pools in the terraform config of [GCP clusters](https://github.com/2i2c-org/infrastructure/blob/d4224ce65d53ee29656bef6d45cbf7f3d0d10df8/terraform/gcp/cluster.tf#L243)
- "nb-<instance-name>" node groups in the eksctl config of [AWS clusters](https://github.com/2i2c-org/infrastructure/blob/d4224ce65d53ee29656bef6d45cbf7f3d0d10df8/eksctl/template.jsonnet#L113-L132)
- "user_pool" node pools in the terraform config of [Azure cluster](https://github.com/2i2c-org/infrastructure/blob/d4224ce65d53ee29656bef6d45cbf7f3d0d10df8/terraform/azure/main.tf#L138-L163)
```

We default to always having available three machine types of 4 / 16 / 64 CPU and a memory specification of 32 / 128 / 512 GB for each user server node pool in a 2i2c cluster. These three options have proven to be general enough to cover most usage scenarios, including events as well as being a good trade off between available options and the maintainability toil.

```{note}
The actual CPU and memory capacity available for use in k8s are slightly lower than the instance specification and dependent on cloud provider and instance type.
```

The three machine types based on the cloud provider are the following:
- [GKE](https://cloud.google.com/compute/docs/general-purpose-machines)
  - n2-highmem-4
  - n2-highmem-16
  - n2-highmem-64
- [EKS](https://aws.amazon.com/ec2/instance-types/r5/)
  - r5.xlarge
  - r5.4xlarge
  - r5.16xlarge
- [AKS](https://learn.microsoft.com/en-us/azure/virtual-machines/eav4-easv4-series)
  - Standard_E4s_v5
  - Standard_E16s_v5
  - Standard_E64s_v5

## Network Policy

When hubs belonging to multiple organizations are run on the same cluster,
we **must** enable [NetworkPolicy enforcement](https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy)
to isolate them from each other.

## Cloud access credentials for hub users

For hub users to access cloud resources like storage buckets from their user
servers, they will need to have credentials from a cloud specific service
account - like a [GCP ServiceAccount].

Currently for practical reasons we only provision one cloud specific service
account per hub, which makes all users interaction be seen as a single user.
Note that providing for example two cloud service accounts, one for hub admin
users and one for non-admin users is by far an easier improvement than providing
one for each hub user.

```{note} Technical notes
When we create a hub with access to a bucket, we create cloud provider specific
service account for the hub via `terraform`. We then also create a [Kubernetes
ServiceAccount] via the basehub chart's templates that references the cloud
specific service account via an annotation. When this Kubernetes ServiceAccount
is mounted to the hub's user server pods, a cloud specific controller ensures
the Pod gets credentials that can be exchanged for temporary credentials to the
cloud specific service account.

[gcp serviceaccount]: https://cloud.google.com/iam/docs/service-accounts
[kubernetes serviceaccount]: https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/
```
