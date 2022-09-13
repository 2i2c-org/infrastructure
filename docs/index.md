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

## How-to guides

How-To guides answer the question 'How do I...?' for a lot of topics.

```{toctree}
:maxdepth: 2
:caption: How-to guides
howto/operate/index.md
howto/hubs/index.md
howto/features/index
howto/k8s/index.md
howto/configure/auth-management/index.md
howto/configure/update-env
howto/cloud/new-gcp-project
howto/support/index
```

## Topic guides

Topic guides go more in-depth on a particular topic.

```{toctree}
:caption: Topic guides
:maxdepth: 2
topic/config.md
topic/cloud-auth.md
topic/features.md
topic/credits.md
topic/hub-helm-charts.md
topic/hub-image.md
topic/storage-layer.md
topic/network.md
topic/terraform.md
topic/cluster-design.md
topic/secrets.md
topic/troubleshooting.md
```

## Reference

Reference information about our infrastructure.

```{toctree}
:caption: Reference
:maxdepth: 2

reference/hubs
reference/ci-cd/index
reference/terraform.md
reference/tools
```

## Contributing

Information on contributing to this repository

```{toctree}
:caption: Contributing
:maxdepth: 2

contributing/code-review
```
