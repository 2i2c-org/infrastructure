# Documentation Structure

We primarily offer documentation, peace of mind and expertise to
our users - and code/configuration is simply an implementation
detail. Well structured documentation aimed at different audiences is
essential to 2i2c's long term health. This document lists the audiencs
we serve, what kinda docs they might expect, and where we provide them.

## Audiences

For each feature we add or change we make, we should create & update
documentation for all of these audiences, as applicable. There are

## For the general public

People visit our website to learn about us, and investigate if we could
be of use to them. Communicating what value we can add to them is 
extremely important, so any feature we write should be integrated into
[our website](https://2i2c.org/infrastructure/). The focus should
be on the value we can add to potential users, and should link to
other kinda documentation for more detail if needed.

## For hub users

Ultimately, our hubs are built to serve researchers, students and instructors. These are our *end users*, and they need to be able to
get their work done. The infrastructure we provide is primarily
opinionated bundles of upstream software, so we don't *need* to rewrite
documentation for all the software they might use. So we should provide
at least the following kinds of documentation:

1. **Tutorials** for common workflows on our infrastructure, since this is heavily driven by the opinionated choices we have made while building it.
3. **How-to guides** to help users accomplish a specific well defined task, especially if it is something they know how to do in a different system.
2. **Component reference** to inform users where to find documentation for the component they might be having issues with. Most users are unfamiliar with the intricate details of what component does what, so might not be able to find the appropriate place to look at.j

## For hub administrators

Hub administrators are the interface between the 2i2c engineers running
the hub and the actual users of the hub. They are usually a part of the
community using the hub, and are interested in the *configuration* of
the hub infrastructure as well. They shoudl be aware of possible
configuration options they can choose to serve their community best, and
be empowered to make those choices without interaction with 2i2c
engineers wherever possible. 

They help make decisions about the configuration of the hub that benefits
its users most, and hence we should provide at least the following kinds
of documentaiton.

1. **Configuration guides** to help them pick the configuration that
   will be best fit for each of our major features - such as
   authentication, kind of user interface, etc.
2. **Self-serve guides** to allow them to do as many *safe*
   configuration changes as quickly as possible without having to
   involving 2i2c engineers. This will also help surface issues that are
   in need of more automation on 2i2c's side.

This documentation should exist in the [2i2c-org/pilot-hubs](https://github.com/2i2c-org/pilot-hubs)

## For 2i2c engineers

These are folks tasked with building, maintaining, debugging and fixing
2i2c infrastructure. Documentation targetting them should be in this
repository (2i2c-org/pilot-hubs), regardless of the kind of hub it 
relates to. Since we run our hubs openly, with best practices that can
ba adopted by anyone, we should try write 
possible.

Here are some contexts where they would need documentation.

1. **Tutorials**, to help orient folks who might be working on areas
   they aren't already familiar with.
2. **How-to guides** for performing common tasks that have not been automated yet.
3. 

