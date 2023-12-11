# Decide if the infrastructure needs preparation before an Event

A hub's specific setup is usually optimized based on the day to day usage expectations. But because events usually imply a different usage pattern, the infrastructure might need to be adjusted in order to accommodate the spikes in activity.

The communities we serve have the responsibility to notify us about an event they have planned on a 2i2c hub [at least three weeks before](https://docs.2i2c.org/community/events/#notify-the-2i2c-team-about-the-event) the event will start. This should allow us enough time to plan and prepare the infrastructure for the event properly if needed.

The events might vary in type, so the following list is not complete and does not cover all of them (yet) Most common event types are exams, workshops etc.

## Event checklist

Below are listed the main aspects to consider adjusting on a hub to prepare it for an event:

### 1. Check the quotas

We must ensure that the quotas from the cloud provider are high-enough to handle expected usage. It might be that the number of users attending the event is very big, or their expected resource usage is big, or both. Either way, we need to check the the existing quotas will accommodate the new numbers.

```{tip}
- follow the [AWS quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in an AWS project
- follow [GCP quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) for information about how to check the quotas in a GCP project
```

### 2. Consider dedicated nodepools on shared clusters

If the hub that's having an event is running on a shared cluster, then we might want to consider putting it on a dedicated nodepool as that will help with cost isolation, scaling up/down effectively, not impacting other hub's users performance.

```{tip}
Follow the guide at [](features:shared-cluster:dedicated-nodepool) in order to setup a dedicated nodepool before an event.
```

### 3. Pre-warm the hub to reduce wait times

There are two mechanisms that we can use to pre-warm a hub before an event:
  - making sure some **nodes are ready** when users arrive

    This can be done using node sharing via profile lists or by setting a minimum node count.
    ```{note}
    You can read more about what to consider when setting resource allocation options in profile lists in [](topic:resource-allocation).
    ```

  - the user **image is not huge**, otherwise pre-pulling it must be considered


Specifically for events, the node sharing benefits via profile lists vs. setting a minimum node count are:

  - **no `terraform/eks` infrastructure changes**

    they shouldn't require modifying terraform/eks code in order to change the underlying cluster architecture thanks to [](topic:cluster-design:instance-type) that should cover most usage needs

  - **more cost flexibility**

    we can setup the infrastructure a few days before the event by opening a PR, and then just merge it as close to the event as possible. Deploying an infrastructure change for an event a few days before isn't as costly as starting "x" nodes before, which required an engineer to be available to make terraform changes as close to the event as possible due to costs

  - **less engineering intervention needed**

    the instructors are empowered to "pre-warm" the hub by starting notebook servers on nodes they wish to have ready.

```{warning}
However, for some communities that don't already use profile lists, setting up one just before an event might be confusing, we might want to consider setting up a minimum node count in this case.
```

#### 3.1. Using node sharing

```{important}
Currently, this is the recommended way to prepare a hub before an event if the hub uses profile lists.
```

Assuming this hub already has a profile list, before an event, you should check the following:

1. **Information is avalailable**

    Make sure the information in the event GitHub issue was filled in, especially the number of expected users before an event and their expected resource needs (if that can be known by the community beforehand).

2. **Given the current setup, calculate**

  - how many users will fit on a node?
  - how many nodes will be necessary during the event?

3. **Check some rules**

    With the numbers you got, check the following general rules are respected:

    - **Startup time**
      - have at least `3-4 people on a node` but [no more than ~100]( https://kubernetes.io/docs/setup/best-practices/cluster-large/#:~:text=No%20more%20than%20110%20pods,more%20than%20300%2C000%20total%20containers) as few users per node cause longer startup times
      - `no more than 30% of the users waiting for a node` to come up
    - For events, we wish to enforce memory constraints that can easily be observed and understood. We might want to consider having an oversubscription factor of 1.
       With this setup, when the limit is reached, the process inside container will be killed and typically in this situation, the kernel dies.


3. **Tilt the balance towards reducing server startup time**

https://infrastructure.2i2c.org/topic/resource-allocation/#factors-to-balance

#### 3.2. By setting a minimum node count for the autoscaler on a specific node pool


