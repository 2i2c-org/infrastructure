# Cluster design considerations

## GKE

## Core node size

In each cluster, we have a *core node pool* that is fairly static in size
and always running. It needs enough capacity to run:

1. Kubernetes system components - network policy enforcement, config connector
   components, cluster autoscaler, kube-dns, etc.

2. Per-cluster support components - like prometheus, grafana, cert-manager,
   etc.

3. Hub core components - the hub, proxy, userscheduler, etc

4. (Optional) Dask gatway core components - the API gateway, controller, etc.

Since the core nodes are *always running*, they form a big chunk of the
cluster's *base cost* - the amount of money it costs each day, regardless
of current number of running users. Picking an apporpriate node size and
count here has a big effect.

### On GKE

GKE makes sizing this nodepool difficult, since `kube-system` components can take up quite
a bit of resources. Even though the kind of clusters we run will most likely
not stress components like `kube-dns` that much, there's no option to provide
them fewer resource requests. So this will be our primary limitation in
many ways.

Adding [Config Connector](https://cloud.google.com/config-connector/docs/overview)
or enabling [Network Policy](https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy)
requires more resources as well.

With poorly structured experimentation, the current recommendation is to run
3 `n1-highmem-2` instances for a cluster without config connector or network policy,
or a single `n1-highmem-4` instance for a cluster with either of those options
turned on. This needs to be better investigated.

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
