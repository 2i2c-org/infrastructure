# Decide if the infrastructure needs preparation before an Event

A hub's specific setup is usually optimized based on the day to day usage expectations. But because events provide a different pattern of usage, the infrastructure might need to be adjusted in order to accommodate the spikes in activity.

The communities we serve have the responsibility to notify us about an event they have planned on a 2i2c hub [at least three weeks before](https://docs.2i2c.org/community/events/#notify-the-2i2c-team-about-the-event) the event will start. This should allow us enough time to plan and prepare the infrastructure for the event properly if needed.

The events might vary in type, so the following list is not complete and does not cover all of them (yet).

Most common event types are:

1. Exams
2. Workshops

## Event checklist

Below are listed the main aspects to consider adjusting to prepare a hub for an event:

### 1. Quotas

We must ensure that the quotas from the cloud provider are high-enough to handle expected usage. It might be that the number of users attending the event is very big, or their expected resource usage is big, or both. Either way, we need to check the the existing quotas will accommodate the new numbers.

- [AWS quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) has information about how to check the quotas in an AWS project 
- [GCP quota guide](hub-deployment-guide:cloud-accounts:aws-quotas) has information about how to check the quotas in a GCP quotas

### 2. Dedicated nodepool - shared clusters

If the hub that's having an event is running on a shared cluster, then we might want to consider putting it on a dedicated nodepool as that will help with cost isolation, scaling up/down effectively, not impacting other hub's users performance.

Follow the guide at [](features:shared-cluster:dedicated-nodepool) in order to setup a dedicated nodepool before an event.

### 3. Pre-warming

There are two mechanisms that we can use to pre-warm a hub before an event: using node sharing via profile lists and by setting a minimum node count.

```{note}
You can read more about what to consider when setting resource allocation options in profile lists in [](topic:resource-allocation).
```

Specifically for events, the node sharing benefits via profile lists vs. setting a minimum node count are:

- it shouldn't require modifying terraform/eks code in order to change the underlying cluster architecture thanks to our [](topic:cluster-design:instance-type) that should cover most usage needs
- we can setup the infrastructure a few days before the event by opening a PR, and then just merge it as close to the event as possible. Deploying an infrastructure change for an event a few days before isn't as costly as starting "x" nodes before, which required an engineer to be available to make terraform changes as close to the event as possible due to costs
- the instructors are empowered to "pre-warm" the hub by starting notebook servers on nodes they wish to have ready.

```{warning}
However, for some communities that don't already use profile lists, setting up one just before an event might be confusing, we might want to consider setting up a minimum node count in this case.
```

#### 3.1. Using node sharing

```{important}
Currently, this is the recommended way to prepare a hub before an event if the hub uses profile lists already.
```

#### 3.2. By setting a minimum node count for the autoscaler on a specific node pool


