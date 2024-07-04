# 2i2c Infrastructure Guide

This is documentation about the infrastructure behind 2i2c's Managed JupyterHubs Service.
The goal of this stack is to automatically deploy JupyterHubs in the cloud with configuration from `config/clusters`.

:::{note}
This documentation is primarily for the 2i2c Open Engineering team.
It describes the details of our cloud deployments, how to operate and improve them, how to debug cloud infrastructure problems, etc.
It is **not** necessary reading for Hub Administrators, but we invite you to explore in order to understand our infrastructure better, and gain inspiration if you're running a similar service.
For documentation about **administering** a 2i2c JupyterHub, see [the 2i2c Hub Administrator's guide](https://docs.2i2c.org).
:::

## Get started

These sections help you get started working with 2i2c's infrastructure.
[](structure) provides a high-level guide to this documentation, and our tutorials are step-by-step guides to help you understand and use our infrastructure.

```{toctree}
:maxdepth: 1
:caption: Get started
structure
tutorials/setup.md
```

(sre-guide)=
## Site reliability engineering guide

The SRE guide covers day-to-day tasks undertaken by engineers as well as tasks that may need to be completed as part of our [support process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/support.html).
We also document common problems and their solutions within these sections, where a permanent solution has not been developed (yet).

```{toctree}
:maxdepth: 1
:caption: SRE guide
sre-guide/support/index.md
sre-guide/manage-k8s/index.md
sre-guide/node-scale-up/index.md
sre-guide/common-problems-solutions.md
```

(hub-deployment-guide)=
## Hub deployment guide

These sections walk an engineer step-by-step through the workflow of setting up a new 2i2c-managed JupyterHub.

```{toctree}
:maxdepth: 1
:caption: Hub deployment guide
hub-deployment-guide/runbooks/index.md
hub-deployment-guide/new-cluster/index.md
hub-deployment-guide/deploy-support/index.md
hub-deployment-guide/configure-auth/index.md
hub-deployment-guide/hubs/index.md
```

## How-to guides

How-To guides answer the question 'How do I...?' for a lot of topics.
These operations do not fall into day-to-day tasks of the [](sre-guide), nor the
standard operations of [deploying a new hub](hub-deployment-guide), but may be
deployed occasionally as a specific addition.

```{toctree}
:maxdepth: 1
:caption: How-to guides
howto/features/index.md
howto/bill.md
howto/custom-jupyterhub-image.md
howto/prepare-for-events/index.md
howto/manage-domains/index.md
howto/grafana-github-auth.md
howto/update-env.md
howto/upgrade-cluster/index.md
howto/troubleshoot/index.md
howto/regenerate-smce-creds.md
howto/budget-alerts
```

## Topic guides

Topic guides go more in-depth on a particular topic.

```{toctree}
:caption: Topic guides
:maxdepth: 2
topic/new-hub
topic/access-creds/index.md
topic/infrastructure/index.md
topic/billing/index.md
topic/monitoring-alerting/index.md
topic/features.md
topic/resource-allocation.md
```

## Reference

Reference information about our infrastructure.

```{toctree}
:caption: Reference
:maxdepth: 1

reference/hubs
reference/options
reference/ci-cd/index
reference/tools
```

## Contributing

Information on contributing to this repository

```{toctree}
:caption: Contributing
:maxdepth: 2

contributing/code-review
contributing/community-partner
```
