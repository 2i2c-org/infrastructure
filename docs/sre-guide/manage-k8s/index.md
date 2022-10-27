# Manage cloud and Kubernetes infrastructure

There are some cases where you need to inspect or modify actively-running Kubernetes infrastructure, or make changes to the Kubernetes cluster on which our hubs are running.
This is a more manual step than [modifying a hub's configuration](/topic/infrastructure/config) and requires some extra tools, setup, and expertise.
These sections cover how to do this.

## Get started

First off, you'll need to gain access to the Kubernetes cluster.
See the following section for instructions on how to do so.

```{toctree}
:maxdepth: 2
/topic/access-creds/cloud-auth.md
```

## Common operations with Kubernetes

The following sections cover common things that you might need to do using Kubernetes directly.

```{toctree}
:maxdepth: 2
node-administration.md
culling.md
```
