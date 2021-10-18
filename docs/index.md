# 2i2c Infrastructure Guide

This is documentation about the infrastructure behind 2i2c's Managed JupyterHubs Service.
The goal of this stack is to automatically deploy JupyterHubs in the cloud with configuration from `config/hubs`.

:::{note}
This documentation is primarily for the 2i2c Open Engineering team.
It describes the details of our cloud deployments, how to operate and improve them, how to debug cloud infrastructure problems, etc.
It is **not** necessary reading for Hub Administrators, but we invite you to explore in order to understand our infrastructure better, and gain inspiration if you're running a similar service.
For documentation about **administering** a 2i2c JupyterHub, see [the 2i2c Hub Administrator's guide](https://docs.2i2c.org).
:::

Below is a quick introduction of this documentation's structure.

```{toctree}
structure
```

## How-to guides

How-To guides answer the question 'How do I...?' for a lot of topics.

```{toctree}
:maxdepth: 2
:caption: How-to guides
howto/configure/index
howto/customize/index
howto/operate/index
```

## Topic guides

Topic guides go more in-depth on a particular topic.

```{toctree}
:caption: Topic guides
:maxdepth: 2
topic/config.md
topic/hub-templates.md
topic/storage-layer.md
topic/terraform.md
topic/cluster-design.md
topic/secrets.md
topic/troubleshooting.md
```

## Reference

Reference information about the pilot hubs.

```{toctree}
:caption: Reference
:maxdepth: 2

reference/hubs
reference/terraform.md
reference/tools
incidents/index
```

## Contributing

Information on contributing to this repository

```{toctree}
:caption: Contributing
:maxdepth: 2

contributing/code-review
```
