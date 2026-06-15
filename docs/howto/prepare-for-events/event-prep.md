# Event infrastructure preparation checklist

Main aspects to consider adjusting on a hub to prepare it for an event:

## Quotas

We must ensure that the quotas from the cloud provider are high-enough to handle expected usage. It might be that the number of users attending the event is very big, or their expected resource usage is big, or both. Either way, we need to check the the existing quotas will accommodate the new numbers.

```{admonition} Action to take
:class: tip
- follow the [AWS quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in an AWS project
- follow the [GCP quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in a GCP project
```

## On shared GCP clusters, consider dedicated nodepools

```{important}
On AWS, all clusters have dedicated nodepools for each hub.
```

If the hub that's having an event is running on a shared cluster, then we might want to consider putting it on a dedicated nodepool as that will help with cost isolation, scaling up/down effectively, and avoid impacting other hub's users performance.

```{admonition} Action to take
:class: tip
Follow the guide at [](features:shared-cluster:dedicated-nodepool) in order to setup a dedicated nodepool before an event.
```

## Reduce server startup time

There are two components that we can "pre-warm" before an event, to reduce server startup time and make sure are ready to use right away:

- the **user image** through pre-pulling
- user **nodes** though making sure a fair number of them are ready for users

```{warning}
Although both of these approaches are helpful, they also come with an increase in cloud costs and engineering work, so they should be considered keeping these aspects in mind.
```

(pre-pull-image)=
### 1. Pre-pulling the image

This should be considered if either of the following are true:

- the image is huge
- faster server startup times were requested at the cost of the cloud cost increase 

```{admonition} Action to take
:class: tip
Follow the guide at [](pre-pull-user-images) to enable image pre-pulling.
```

### 2. Pre-warming user nodes

This can be done in a few different ways:

- node sharing via profile lists
- setting a minimum node count on a specific node pool
- using node placeholders

```{admonition} However, **the preferred way to do this is through node sharing via profile lists**.
:class: dropdown
Specifically for events, the node sharing benefits via profile lists vs. setting a minimum node count are:

  - **no `terraform/eks` infrastructure changes**

    they shouldn't require modifying terraform/eks code in order to change the underlying cluster architecture thanks to [](topic:cluster-design:instance-type) that should cover most usage needs

  - **more cost flexibility**

    we can setup the infrastructure a few days before the event by opening a PR, and then just merge it as close to the event as possible. Deploying an infrastructure change for an event a few days before isn't as costly as starting "x" nodes before, which required an engineer to be available to make terraform changes as close to the event as possible due to costs

  - **less engineering intervention needed**

    the instructors are empowered to "pre-warm" the hub by starting notebook servers on nodes they wish to have ready.
```

#### 2.1 Node sharing via profile lists

```{important}
Currently, this is the recommended way to handle an event on a hub. However, for some communities that don't already use profile lists, setting up one just before an event might be confusing, we might want to consider setting up a minimum node count in this case.
```

During events, we want to tilt the balance towards reducing server startup time. The docs at [](topic:resource-allocation) have more information about all the factors that should be considered during resource allocation.


Assuming this hub already has a profile list, you should check the following before an event:

```{admonition} 1. **Make sure information is available**
:class: dropdown
Make sure the information in the event GitHub issue was filled in, especially the hub that is going to be used, the number of expected users before an event and their expected resource needs (if that can be known by the community beforehand).
```

```{admonition} 2. **Calculate how many users will fit on a node?**
:class: dropdown
Check that the current number of users/node respects the following general event wishlist.
```

````{admonition} 3. **Choose the node packing**
:class: dropdown
- have at least `3-4 people on a node` as few users per node cause longer startup times, but [no more than ~100](https://kubernetes.io/docs/setup/best-practices/cluster-large/#:~:text=No%20more%20than%20110%20pods,more%20than%20300%2C000%20total%20containers)

- don't have more than 30% of the users waiting for a node to come up

  If the current number of users per node doesn't respect the rules above, you should adjust the instance type so that it does.
  Note that if you are changing the instance type, you should also consider re-writing the allocation options, especially if you are going with a smaller machine than the original one.

  ```{code-block}
  deployer generate resource-allocation choices <instance type>
  ```
````

````{admonition} 4. **Don't oversubscribe resources**
:class: dropdown
The oversubscription factor is how much larger a limit is than the actual request (aka, the minimum guaranteed amount of a resource that is reserved for a container). When this factor is greater, then a more efficient node packing can be achieved because usually most users don't use resources up to their limit, and more users can fit on a node.

However, a bigger oversubscription factor also means that the users that use more resources than they are guaranteed can get their kernels killed or CPU throttled at some other times, based on what other users are doing. This inconsistent behavior is confusing to end users and the hub, so we should try and avoid this during events.

**For an event, you should consider an oversubscription factor of 1.**

- if the instance type remains unchanged, then just adjust the limit to match the memory guarantee if not already the case

- if the instance type also changes, then you can use the `deployer generate resource-allocation` command, passing it the new instance type and optionally the number of choices.

  You can then use its output to:
    - either replace all allocation options with the ones for the new node type
    - or pick the choice(s) that will be used during the event based on expected usage and just don't show the others

```{warning}
The `deployer generate resource-allocation`:
- can only generate options where guarantees (requests) equal limits!
- supports the instance types located in `node-capacity-info.json` file
```
````

### 3.2. Setting a minimum node count on a specific node pool
```{warning}
This section is a Work in Progress!
```

### 3.4 Add user placeholders


#### Introducing user placeholders
Whilst one strategy to minimising startup times is to increase the number of user pods that fit onto a single node (thereby reducing the number of times a node needs to be scaled up across the event), this approach will still introduce waiting points when a scale up is required.

A useful mechanism for reducing the likelihood of a blocking scale up is the use of [user-placeholders](https://z2jh.jupyter.org/en/stable/administrator/optimization.html#scaling-up-in-time-user-placeholders). This technique involves scheduling pods that represent a "seat" or "placeholder" for anticipated user servers. Once users join the cluster, these pods are evicted by the scheduler to make room for the real user pods. 

To illustrate this, consider a hub with a dedicated user nodepool. Each node can support 64 singleuser pods. Let's imagine that the number of user placeholder replicas is set to 32:

- Initially, there will be 32 user placeholder pods running on a single user node.
- For the next 32 users that join, no scaling up will occur, and once all of the users have joined, the node will be "full" with 32 users and 32 placeholders.
- Once the 33rd user joins, one of the user placeholders will be evicted, triggering a scale up to maintain the 32 user-node replica requirement.

Conventionally, one might imaging that the 34th user (and the 35th, etc.) will immediately be able to spawn their server pod, as the scheduler continues to evict pods. In practice this is not what happens. Instead, once the first placeholder pod is evicted and the autoscaler triggers a scale up, subsequent user pods are directly scheduled on the not-yet-ready node. This introduces head-of-line blocking for 31 of these 32 subsequent users.

#### Choosing placeholder resources
As such, it is more effective to create a singular placeholder pods that represents $N$ users. For example, if we wish to reserve capacity for 32 users, and each user is guaranteed 1GiB of memory, then we would create a placeholder pod with a 32GiB memory request. In the extreme case, we might wish to reserve an entire node. We must be careful not to request more RAM than is available _after_ the kube-system pods have been started on the node. In practice, this might mean leaving ~2GiB of memory (though this should be confirmed through testing).

In event conditions, we might anticipate a particular rate at which users attempt to start their servers. Measurements of this value can be derived from previous event instances. If one such event needs to support 60 users every 3 minutes, and it takes 10 minutes for a node to spin up, we will need to have room for $60/3 * 10 = 200$ users. We can compute the appropriate number of resources accordingly.

#### Auxiliary considerations
Simply ensuring that a node is ready to accept user pods is not sufficient to ensure that users do not experience delays when the user node pool is scaled up. In order to start user pods, the cluster needs to pull their respective OCI container images from the container registry. If we do not do this ahead of time, the first user to require a particular image will need to wait for it to be pulled to the cluster, as will all other image users. 

We can anticipate this be pre-pulling the various images required at node startup time, using the continuous image puller (see [](pre-pull-image)). This should only be used on dedicated nodepools in which the number of images is small (as pulling a set of images delays the time until the node is considered available to user pods).

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
