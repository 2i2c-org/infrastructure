(scaling-nodepools:azure)=
# Azure

In certain cases, it might be helpful to 'scale up'
a node group in a cluster before an event, to test cloud provider quotas or to make user
server startup faster.

## Azure Console UI instructions

### Scaling up a node pool

1. Login to https://portal.azure.com using the appropriate cluster credentials

1. Search the `Kubernetes service` section for the appropriate cluster

1. Click on the cluster name, then go to `Settings` and select the `Node pools` option

1. Click on the appropriate node pool that you would like to scale up

1. Then select the `Scale node pool` option from the top of the page

1. A new window should pop up that looks like this

    ```{figure} ../../images/azure-scale-node-pool-window.png
    Scale node pool
    ```

1. If the `Autoscale` option is selected like in the screenshot above (the default, recommended option),
   then in order to scale up the node pool to an exact number of nodes, temporarily deactivate the autoscaler,
   by selecting the `Manual` option, introduce the desired number of nodes then click `Apply`.

1. After the Apply succeeded, you should see the new nodes coming up.
   You can then click on `Scale node pool` option again, **enable the `Autoscale`**,
   and set the `Min` number of nodes to the desired one the you set in the step before.

```{warning}
Don't forget to turn the autoscaler back on after the manual
modification of the node pool size! This is **really important**, otherwise
a scale up from the max manual limit, won't be able to happen automatically,
and the hub won't be able to spawn new user servers.
```

### Scaling down a node pool

1. Follow the first six steps in the scaling up guide above, until you get to the `Scale node pool` window.

1. This time, **do not activate the `Manual` mode**,
   and just adjust the `Min` number of nodes for the autoscaler.
   As users stop their servers after the event, eventually a scale down event will be triggered,
   and the autoscaler will adjust the node pool size according to the limits that are set.

```{note}
The cluster autoscaler doesn't enforce the node pool size after updating the `Min` or `Max` counts.
The limits will be taken into accounts for future scaling decisions.
A new scaling decision happens after a scale up/down event is triggered.

So, because we usually want nodes to be ready and waiting before an event,
and not wait for a scale up/down event, we need to temporarily disable the autoscaler.

More about the Azure autoscaler in the docs [here](https://learn.microsoft.com/en-us/azure/aks/hybrid/work-with-autoscaler-profiles#notes-on-autoscaler-configuration).
```

## Terraform instructions

TODO