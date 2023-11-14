(upgrade-cluster:disruptions)=

# Overview of different kinds of upgrade disruptions

When we upgrade our Kubernetes clusters we can cause different kinds of
disruptions. Below we overview the disruptions impacting users.

## Kubernetes api-server disruption

K8s clusters' control plane (api-server etc.) can be either highly available
(HA) or not. EKS clusters and "regional" GKE clusters are HA, but "zonal" GKE
clusters are not. Upgrading a HA Kubernetes cluster's control plane should by
itself not cause any disruptions.

If you upgrade a non-HA cluster's control plane, it typically takes less time,
only ~5 minutes. During this time user pods and JupyterHub remains accessible,
but JupyterHub won't be able to start new user servers, and user servers won't
be able to create or scale their dask-clusters.

## Core node pool disruptions

Disruptions to the core node pool is a disruption to workloads running on it,
and there are a few workloads that when disrupted would disrupt users.

### ingress-nginx-controller pod(s) disruptions

The `support` chart we install in each cluster comes with the `ingress-nginx`
chart. The `ingress-nginx` chart creates one or more `ingress-nginx-controller`
pods that are proxying network traffic associated with incoming connections.

To shut down such pod means to break connections from users working against the
user servers. A broken connection can be re-established if there is another
replica of this pod is ready to accept a new connection.

We are currently running only one replica of the `ingress-nginx-controller` pod,
and we won't have issues with this during rolling updates, such as when the
Deployment's pod template specification is changed or when manually running
`kubectl rollout restart -n support deploy/support-ingress-nginx-controller`. We
will however have broken connections and user pods unable to establish new
directly if `kubectl delete` is used on this single pod, or `kubectl drain` is
used on the node.

As long as we have one replica, we should to minimize user disruptions do
`kubectl rollout restart -n support deploy/support-ingress-nginx-controller` to
migrate this pod from one node to another before `kubectl drain` is used.

### hub pod disruptions

Our JupyterHub installations each has a single `hub` pod, and having more isn't
supported by JupyterHub itself. Due to this, and because it has a disk mounted
to it that can only be mounted at the same time to one pod, it isn't configured
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

Disruptions to a user node pool is a disruption to user server pods running on
it, and that can't be done gracefully. We lack a detailed recipe on these
situations, but here are strategies to consider.

### Manually terminating inactive servers

The `jupyterhub-idle-culler` is by default configured to shut down inactive user
servers, but sometimes it can fail due to regular irrelevant network activity
for example.

It could be reasonable to consider terminating a user server that _seems_
inactive. Here are some signs of inactivity in a user server:

* `kubectl logs <user pod>` shows no recent activity
* `kubectl top pod <user pod>` shows almost no CPU or memory use

### Slowly phasing out a node pool

Individual node's can be cordoned to not allow scheduling of new pods on them
using `kubectl cordon`. This can help you to get pods to schedule on another
node that perhaps already is upgraded.

### Scheduling maintenance

By scheduling maintenance with the community ahead of time, disruptions of
active user servers during this time could be acceptable.
