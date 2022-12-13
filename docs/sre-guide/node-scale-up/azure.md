(scaling-nodepools:azure)=
# Azure

In certain cases, it might be helpful to 'scale up'
a nodegroup in a cluster before an event, to test cloud provider quotas or to make user
server startup faster.

## Azure Console UI instructions

1. Login to https://portal.azure.com using the appropriate cluster credentials

1. Search the `Kubernetes service` section for the appropriate cluster

1. Click on the cluster name, then go to `Settings` and select the `Node pools` option

1. Click on the appropriate nodepool that you would like to scale up

1. Then select the `Scale node pool` option from the top of the page

1. A new window should pop up that looks like this

```{figure}
../../images/azure-scale-node-pool-window.png
```

1. If the `Autoscale` option is selected like in the screenshot above (the default, recommended option),
   then in order to scale up the nodepool to an exact number of nodes, temporarily deactivate the autoscaler,
   by selecting the `Manual` option, introduce the desired number of nodes then click `Apply`.

1. After the Apply succeded, you should see the new nodes coming up.
   You can then click on `Scale node pool` option again, enable the `Autoscale`,
   and set the min number of nodes to the desired one the you set in the step before.

```{warning}
The cluster autoscaler doesn't enforce the nodepool size after updating the `Min` or `Max` counts.
The limits will be taken into accounts for future scaling decisions.
A new scaling decision happens after a scale up/down event is triggered.

So, because we usually want nodes to be ready and waiting before an event,
and not wait for a scale up/down event, we need to temporarily disable the autoscaler.

More about the Azure autoscaler in the docs [here](https://learn.microsoft.com/en-us/azure/aks/hybrid/work-with-autoscaler-profiles#notes-on-autoscaler-configuration).
```

## Terraform instructions

TODO