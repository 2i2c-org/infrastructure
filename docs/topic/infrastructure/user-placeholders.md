(topic:user-placeholders)=
# User placeholders

Whilst one strategy to minimising startup times is to increase the number of user pods that fit onto a single node (thereby reducing the number of times a node needs to be scaled up across the event), this approach will still introduce waiting points when a scale up is required.

A useful mechanism for reducing the likelihood of a blocking scale up is the use of [user-placeholders](https://z2jh.jupyter.org/en/stable/administrator/optimization.html#scaling-up-in-time-user-placeholders). This technique involves scheduling pods that represent a "seat" or "placeholder" for anticipated user servers. Once users join the cluster, these pods are evicted by the scheduler to make room for the real user pods. 

To illustrate this, consider a hub with a dedicated user nodepool. Each node can support 64 singleuser pods. Let's imagine that the number of user placeholder replicas is set to 32:

- Initially, there will be 32 user placeholder pods running on a single user node.
- For the next 32 users that join, no scaling up will occur, and once all of the users have joined, the node will be "full" with 32 users and 32 placeholders.
- Once the 33rd user joins, one of the user placeholders will be evicted, triggering a scale up to maintain the 32 user-node replica requirement.

Conventionally, one might imaging that the 34th user (and the 35th, etc.) will immediately be able to spawn their server pod, as the scheduler continues to evict pods. In practice this is not what happens. Instead, once the first placeholder pod is evicted and the autoscaler triggers a scale up, subsequent user pods are directly scheduled on the not-yet-ready node. This introduces head-of-line blocking for 31 of these 32 subsequent users.

## Choosing placeholder resources

As such, it is more effective to create a singular placeholder pods that represents $N$ users. For example, if we wish to reserve capacity for 32 users, and each user is guaranteed 1GiB of memory, then we would create a placeholder pod with a 32GiB memory request. In the extreme case, we might wish to reserve an entire node. We must be careful not to request more RAM than is available _after_ the kube-system pods have been started on the node. In practice, this might mean leaving ~2GiB of memory (though this should be confirmed through testing).

In event conditions, we might anticipate a particular rate at which users attempt to start their servers. Measurements of this value can be derived from previous event instances. If one such event needs to support 60 users every 3 minutes, and it takes 10 minutes for a node to spin up, we will need to have room for $60/3 * 10 = 200$ users. We can compute the appropriate number of resources accordingly.

## Auxiliary considerations
Simply ensuring that a node is ready to accept user pods is not sufficient to ensure that users do not experience delays when the user node pool is scaled up. In order to start user pods, the cluster needs to pull their respective OCI container images from the container registry. If we do not do this ahead of time, the first user to require a particular image will need to wait for it to be pulled to the cluster, as will all other image users. 

We can anticipate this be pre-pulling the various images required at node startup time, using the continuous image puller (see [](#pre-pull-image)). This should only be used on dedicated nodepools in which the number of images is small (as pulling a set of images delays the time until the node is considered available to user pods).

An example configuration might look something like
```yaml
jupyterhub:
  prePuller:
    continuous:
      enabled: true
  scheduling:
    userPlaceholder:
      # Keep at least half of a 64 GiB node free
      replicas: 1
      resources:
        requests:
          memory: 32Gi
```
