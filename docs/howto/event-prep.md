# Decide if the infrastructure needs preparation before an Event

A hub's specific setup is usually optimized based on the day to day usage expectations. But because events usually imply a different usage pattern, the infrastructure might need to be adjusted in order to accommodate the spikes in activity.

```{important}
The communities we serve have the responsibility to notify us about an event they have planned on a 2i2c hub [at least three weeks before](https://docs.2i2c.org/community/events/#notify-the-2i2c-team-about-the-event) the event will start. This should allow us enough time to plan and prepare the infrastructure for the event properly if needed.
```

The events might vary in type, so the following list is not complete and does not cover all of them (yet). Most common event types are exams, workshops etc.

## Event checklist

Below are listed the main aspects to consider adjusting on a hub to prepare it for an event:

### 1. Quotas

We must ensure that the quotas from the cloud provider are high-enough to handle expected usage. It might be that the number of users attending the event is very big, or their expected resource usage is big, or both. Either way, we need to check the the existing quotas will accommodate the new numbers.

```{admonition} Action to take
:class: tip
- follow the [AWS quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in an AWS project
- follow the [GCP quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in a GCP project
```

### 2. Consider dedicated nodepools on shared clusters

If the hub that's having an event is running on a shared cluster, then we might want to consider putting it on a dedicated nodepool as that will help with cost isolation, scaling up/down effectively, and avoid impacting other hub's users performance.

```{admonition} Action to take
:class: tip
Follow the guide at [](features:shared-cluster:dedicated-nodepool) in order to setup a dedicated nodepool before an event.
```

### 3. Pre-warm the hub to reduce wait times

There are two mechanisms that we can use to pre-warm a hub before an event:

- making sure some **nodes are ready** when users arrive

    This can be done using node sharing via profile lists or by setting a minimum node count.
  
    ```{note}
    You can read more about what to consider when setting resource allocation options in profile lists in [](topic:resource-allocation).
    ```

    ```{admonition} Expand this to find out the benefits of node sharing via profile lists
    :class: dropdown
    Specifically for events, the node sharing benefits via profile lists vs. setting a minimum node count are:

      - **no `terraform/eks` infrastructure changes**

        they shouldn't require modifying terraform/eks code in order to change the underlying cluster architecture thanks to [](topic:cluster-design:instance-type) that should cover most usage needs

      - **more cost flexibility**

        we can setup the infrastructure a few days before the event by opening a PR, and then just merge it as close to the event as possible. Deploying an infrastructure change for an event a few days before isn't as costly as starting "x" nodes before, which required an engineer to be available to make terraform changes as close to the event as possible due to costs

      - **less engineering intervention needed**

        the instructors are empowered to "pre-warm" the hub by starting notebook servers on nodes they wish to have ready.
    ```

- the user **image is not huge**, otherwise pre-pulling it must be considered


#### 3.1. Node sharing via profile lists

```{important}
Currently, this is the recommended way to handle an event on a hub. However, for some communities that don't already use profile lists, setting up one just before an event might be confusing, we might want to consider setting up a minimum node count in this case.
```

During events, we want to tilt the balance towards reducing server startup time. The docs at [](topic:resource-allocation) have more information about all the factors that should be considered during resource allocation.

Assuming this hub already has a profile list, before an event, you should check the following:

1. **Information is available**

    Make sure the information in the event GitHub issue was filled in, especially the number of expected users before an event and their expected resource needs (if that can be known by the community beforehand).

2. **Given the current setup, calculate how many users will fit on a node?**

    Check that the current number of users/node respects the following general event wishlist.

3. **Minimize startup time**

  - have at least `3-4 people on a node` as few users per node cause longer startup times, but [no more than ~100]( https://kubernetes.io/docs/setup/best-practices/cluster-large/#:~:text=No%20more%20than%20110%20pods,more%20than%20300%2C000%20total%20containers)
  - don't have more than 30% of the users waiting for a node to come up

    ````{admonition} Action to take
    :class: tip

    If the current number of users per node doesn't respect the rules above, you should adjust the instance type so that it does.
    Note that if you are changing the instance type, you should also consider re-writing the allocation options, especially if you are going with a smaller machine than the original one.

    ```bash
    deployer generate resource-allocation choices <instance type>
    ```
    ````

4. **Don't oversubscribe resources**
    The oversubscription factor is how much larger a limit is than the actual request (aka, the minimum guaranteed amount of a resource that is reserved for a container). When this factor is greater, then a more efficient node packing can be achieved because usually most users don't use resources up to their limit, and more users can fit on a node.

    However, a bigger oversubscription factor also means that the users that use more resources than they are guaranteed can get their kernels killed or CPU throttled at some other times, based on what other users are doing. This inconsistent behavior is confusing to end users and the hub, so we should try and avoid this during events.

    ````{admonition} Action to take
    :class: tip

    For an event, you should consider an oversubscription factor of 1. For this you can use the deployer script by passing it the instance type where the pods will be scheduled on (in this example is `n2-highmem-4`), then from its output, pick the choice(s) that will be used during the event based on expected usage.

    ```bash
    deployer generate resource-allocation choices n2-highmem-4
    ```
    ````


#### 3.2. Setting a minimum node count on a specific node pool
```{warning}
This section is a Work in Progress!
```

#### 3.3. Pre-pulling the image

```{warning}
This section is a Work in Progress!
```

Relevant discussions:
- https://github.com/2i2c-org/infrastructure/issues/2541
- https://github.com/2i2c-org/infrastructure/pull/3313
- https://github.com/2i2c-org/infrastructure/pull/3341

```{important}
To get a deeper understanding of the resource allocation topic, you can read up these issues and documentation pieces:
- https://github.com/2i2c-org/infrastructure/issues/2121
- https://github.com/2i2c-org/infrastructure/pull/3030
- https://github.com/2i2c-org/infrastructure/issues/3132
- https://github.com/2i2c-org/infrastructure/issues/3293
- https://infrastructure.2i2c.org/topic/resource-allocation/#factors-to-balance
```