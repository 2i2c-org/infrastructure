# Event infrastructure preparation checklist

Main aspects to consider adjusting on a hub to prepare it for an event:

## Quotas

We must ensure that the quotas from the cloud provider are high-enough to handle expected usage. It might be that the number of users attending the event is very big, or their expected resource usage is big, or both. Either way, we need to check the the existing quotas will accommodate the new numbers.

```{admonition} Action to take
:class: tip
- follow the [AWS quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in an AWS project
- follow the [GCP quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in a GCP project
```

## Consider dedicated nodepools

```{important}
On AWS, clusters already have dedicated nodepools for each hub.
```

If the hub that's having an event is running on a shared cluster, then we might want to consider putting it on a dedicated nodepool as that will help with cost isolation, scaling up/down effectively, and avoid impacting other hub's users performance.

```{admonition} Action to take
:class: tip
Follow the guide at [](features:shared-cluster:dedicated-nodepool) in order to setup a dedicated nodepool before an event.
```

## Analyze Grafana workshop dashboard results
```{warning}
This is a work in progress.
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

```{admonition} Action to take
:class: tip
Follow the guide at [](scaling-nodepools) to on how to set a minimum node count on a specific node pool.
```

### 3.4 Add user placeholders
```{warning}
This section is a work in progress.
```

Checkout [](topic:user-placeholders) to find out more about this topic

## Evaluate scratch space needs

```{warning}
This section is a work in progress.
```

See https://github.com/2i2c-org/initiatives/issues/61 for more details on the progress of this topic.