# Conventions

## Workspaces

We use [terraform workspaces](https://www.terraform.io/docs/language/state/workspaces.html)
to maintain separate terraform states about different clusters we manage.
There should be one workspace per cluster, with the same name as the `.tfvars`
file with variable definitions for that cluster.

Workspaces are stored centrally in the `two-eye-two-see-org` GCP project, even
when we use Terraform for projects running on AWS / Azure. You must have
access to this project before you can use terraform for our infrastructure.

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
3 `g1-small` instances for a cluster without config connector or network policy,
or a single `n1-highmem-4` instance for a cluster with either of those options
turned on. This needs to be better investigated.