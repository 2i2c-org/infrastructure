# Add a new hub

This section describes steps around adding new hubs to the 2i2c JupyterHub federation.

## General overview

We use a GitHub Issue Template to keep track of the to-do items in creating a new hub.
The best way to understand the information and steps needed for this process is in that template.
Below is a short overview of the steps in the process.

1. [Create a new GitHub issue for the hub](https://github.com/2i2c-org/pilot-hubs/issues/new?assignees=&labels=type%3A+hub&template=new-hub.md&title=New+Hub%3A+%5BHub+name%5D).
   The following steps are major sections described in the template.
2. Collect information about the hub that helps us deploy it in the proper manner (see the issue template for explanations about the information we need).
3. Create the hub via appending a new hub entry in the appropriate cluster file under
   `config/hubs` file (see [](../../topic/config.md) for more information).
4. Start following [team process](team-process) around operating the hubs.

## Cloud provider-specific information

The following sections contain information that is unique to each cloud provider.
Follow these guides in addition to the more general instructions above.

```{toctree}
add-aws-hub.md
```
