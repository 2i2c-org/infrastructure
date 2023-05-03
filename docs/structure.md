# Documentation structure

This page describes how the documentation we maintain at
<https://infrastructure.2i2c.org> is structured.

## Audience

The primary audience of this documentation is
[**2i2c Engineers**](https://compass.2i2c.org/en/latest/engineering/structure.html#open-source-infrastructure-engineer),
though anyone is welcome to peruse them for their own understanding if they wish.

Engineers are folks tasked with building, maintaining, debugging and fixing
2i2c infrastructure. Since we run our hubs openly, with best practices that can
be adopted by anyone, we should try write these to be as accessible to
non 2i2c staff as possible - no secret sauce, minimal 2i2c specific
process.

## Structure

Infrastructure documentation is broken down into these main guides:

- [**Site Reliability Guide.**](sre-guide) This guide covers day-to-day tasks
  undertaken by engineers as well as tasks that may need to be completed as part
  of the
  [support process](https://team-compass.2i2c.org/en/latest/projects/managed-hubs/support.html).
  It is also a place to document common problems and their solutions for future
  reference.
- [**Hub Deployment Guide.**](hub-deployment-guide) This guide walks an engineer
  through the process of deploying a hub, step-by-step. It should document how
  to enable all the features we typically enable during a standard hub deployment.

The remainder of our documentation is organised as such:

- **"Get Started"** tutorials help orient folks who might be working on areas
  they aren't already familiar with and help them achieve a specific goal. These
  articles should have clear links to pre-requisite knowledge and how it can be
  acquired.
- **How-to guides** demonstrate how to perform tasks that have not been automated
  yet, or enable extra features that are not part of a standard hub deployment.
  The titles of these guides should be of the form **How do I `<title>`?**
- **Topic guides** go into greater depth of conceptual ideas around our
  infrastructure, why we deploy things the way we do, and what steps we have
  taken to automate some tasks. These articles are grouped together by a broad
  topic, such as "monitoring and alerting". If the topic guide you are writing
  doesn't belong to one of the pre-existing groups, feel free to create a new
  group if you suspect we will generate more documentation for that topic, or
  create it as a standalone article, such as the [](hub-features) article.
- **References** describe in detail parts of our infrastructure and its
  configuration. This should ideally be kept in the code describing our
  infrastructure - for example,
  [terraform-docs](https://github.com/terraform-docs/terraform-docs) for
  terraform code, JSON Schema based document generator for YAML, etc. This helps
  them keep in sync with what we are actually doing.
