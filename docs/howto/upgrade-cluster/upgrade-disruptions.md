(upgrade-cluster:disruptions)=

# About upgrade disruptions

When we upgrade our Kubernetes clusters we can cause different kinds of
disruptions, this text provides an overview of them.

## Kubernetes api-server disruption

K8s clusters' control plane (api-server etc.) can be either highly available
(HA) or not. EKS clusters, AKS clusters, and "regional" GKE clusters are HA, but
"zonal" GKE clusters are not. A few of our GKE clusters are zonal still, but as
the cost savings are minimal we only create for regional clusters now.

If upgrading a zonal cluster, the single k8s api-server will be temporarily
unavailable, but that is not a big problem as user servers and JupyterHub will
remain accessible. The brief disruption is that JupyterHub won't be able to
start new user servers, and user servers won't be able to create or scale their
dask-clusters.

## Provider managed workload disruptions

When upgrading a cloud provider managed k8s cluster, it may upgrade some managed
workload part of the k8s cluster, such as calico that enforces NetworkPolicy
rules. Maybe this could cause a disruption for users, but its not currently known
if it does and in what manner.

## Core node pool disruptions

Disruptions to the core node pool is a disruption to workloads running on it,
and there are a few workloads that when disrupted would disrupt users.

### ingress-nginx-controller pod(s) disruptions

The `support` chart we install in each cluster comes with the `ingress-nginx`
chart. The `ingress-nginx` chart creates one or more `ingress-nginx-controller`
pods that are proxying network traffic associated with incoming connections.

To shut down such pod means to break connections from users working against the
user servers. A broken connection can be re-established if there is another
replica of this pod ready to accept a new connection.

We are currently running only one replica of the `ingress-nginx-controller` pod,
and we won't have issues with this during rolling updates, such as when the
Deployment's pod template specification is changed or when manually running
`kubectl rollout restart -n support deploy/support-ingress-nginx-controller`. We
will however have broken connections and user pods unable to establish new connections
directly if `kubectl delete` is used on this single pod, or `kubectl drain` is
used on the node.

### hub pod disruptions

Our JupyterHub installations each have a single `hub` pod, and having more isn't
supported by JupyterHub itself. Due to this, and because it has a disk mounted
to it that can only be mounted to one pod at a time, it isn't configured
to do rolling updates.

When the `hub` pod isn't running, users can't visit `/hub` paths, but they can
still visit `/user` paths and control their already started user server.

### proxy pod disruptions

Our JupyterHub installations each has a single `proxy` pod running
`configurable-http-proxy`, having more replicas isn't supported because
JupyterHub will only update one replica with new proxy routes.

When the `proxy` pod isn't running, users can't visit `/hub`, `/user`, or
`/service` paths, because they all route through the proxy pod.

When the `proxy` pod has started and become ready, it also needs to be
re-configured by JupyterHub on how to route traffic to arrive to `/user` and
`/service` paths. This is done during startup and then regularly by JupyterHub
every five minutes. Due to this, a proxy pod being restarted can cause a outage
of five minutes.

## User node pool disruptions

Disruptions to a user node pool will disrupt user server pods running on it.
