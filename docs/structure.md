# Documentation structure

We primarily offer documentation, peace of mind and expertise to
our users - and code/configuration is simply an implementation
detail. Well structured documentation aimed at different audiences is
essential to 2i2c's long term health. This document lists the audiencs
we serve, what kinda docs they might expect, and where we provide them.

## Audiences

For each feature we add or change we make, we should create & update
documentation for all of these audiences, as applicable. There are a
few key audiences that are outlined below.

## The general public

People visit our website to learn about us, and investigate if we could
be of use to them. Communicating what value we can add to them is
extremely important, so any feature we write should be integrated into
[our website](https://2i2c.org/). The focus should
be on the value we can add to potential users, and should link to
other kinda documentation for more detail if needed.

## Hub users

Ultimately, our hubs are built to serve researchers, students and instructors.
These are our *end users*, and they need to be able to
get their work done.

The infrastructure we provide is primarily opinionated bundles of
upstream software, so we don't *need* to rewrite documentation for all
the software they might use. However, since we make opinionated choices
about JupyterHub deployments, some repetition of upstream documentation
that assumes the specific choices we already make is helpful.

We should provide at least the following kinds of documentation:

1. **Tutorials** for common workflows on our infrastructure, since this is
   heavily driven by the opinionated choices we have made while building it.
2. **How-to guides** to help users accomplish a specific well defined task,
   especially if it is something they know how to do in a different system.
   The documentation titles should always be of the form **How do I `<title>`?**
3. **Component reference** to inform users where to find documentation for
   the component they might be having issues with. Most users are unfamiliar
   with the intricate details of what component does what, so might not be
   able to find the appropriate place to look at.

This documentation should exist in the [2i2c-org/docs](https://github.com/2i2c-org/docs)
repository, available at [docs.2i2c.org](https://docs.2i2c.org)

## Hub administrators

Hub administrators are the interface between the 2i2c engineers running
the hub and the actual users of the hub. They are usually a part of the
community using the hub, and are interested in the *configuration* of
the hub infrastructure as well. They should be aware of possible
configuration options they can choose to serve their community best, and
be empowered to make those choices without interaction with 2i2c
engineers wherever possible.

They help make decisions about the configuration of the hub that benefits
its users most, and hence we should provide at least the following kinds
of documentaiton.

1. **Configuration guides** to help them *pick* the configuration that
   will be best fit for each of our major features - such as
   authentication, kind of user interface, etc. Their hubs are then
   configured with these choices in collaboration with 2i2c staff. Each
   guide should mention *how* this implementation can occur - possibly
   with a link to documentation for 2i2c engineers  .
2. **How-to guides** to help admins accomplish very specific tasks during
   the course of hub usage. Their titles should always be of the form
   **How do I `<title>`?**.

This documentation should exist in the [2i2c-org/docs](https://github.com/2i2c-org/docs)
repository, available at [docs.2i2c.org](https://docs.2i2c.org/)

## 2i2c engineers

These are folks tasked with building, maintaining, debugging and fixing
2i2c infrastructure. Documentation targetting them should be in
[2i2c-org/infrastructure](https://github.com/2i2c-org/infrastructure)
repository, regardless of the kind of hub it
relates to. Since we run our hubs openly, with best practices that can
be adopted by anyone, we should try write these to be as accessible to
non 2i2c staff as possible - no secret sauce, minimal 2i2c specific
process.

Here are some contexts where they would need documentation.

1. **Tutorials**, to help orient folks who might be working on areas
   they aren't already familiar with. This should have clear links to
   pre-requisite knowledge and how it can be acquired.
2. **How-to guides** for performing common tasks that have not been
   automated yet. Their titles should always be of the form
   **How do I `<title>`?**
3. **Topic guides**
4. **References**, describing in detail parts of our infrastructure and
   its configuration. This should ideally be kept in the code describing
   our infrastructure - for example, [terraform-docs](https://github.com/terraform-docs/terraform-docs)
   for terraform code, JSON Schema based document generator for YAML,
   etc. This helps them be in sync with what we are actually doing.
