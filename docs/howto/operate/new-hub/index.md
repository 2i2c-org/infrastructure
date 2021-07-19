# Add a new hub

This section describes steps around adding new hubs to the 2i2c JupyterHub federation.

## General overview

We use a GitHub Issue Template to keep track of the to-do items in creating a new hub.
Below is a short overview of the steps in the process.

1. [Create a new GitHub issue for the hub](https://github.com/2i2c-org/pilot-hubs/issues/new).
   The following steps are major sections described in the template.
2. Collect information about the hub that helps us deploy it in the proper manner (see the issue template for explanations about the information we need).
3. Create the hub via appending a new hub entry in the appropriate cluster file under
   `config/hubs` file (see [](../../topic/config.md) for more information).
4. Start following [team process](team-process) around operating the hubs.

## Information needed to deploy a new hub

Here's a short description of the major pieces of information we need per hub.
These should be listed in the Issue Template for a new hub.

### Community information

Hub Representative
: The main point-of-contact for this hub, and the person who requests changes to the hub on behalf of the community.
  Should be either a GitHub handle or email address.
Target start date
: The target start date when this hub will begin operation.
  This should be at least a week before any important usage of the hub will occur, to ensure that the Hub Representative has time to try it out. 
Important dates
: Any important dates that we should consider for this hub.
  For example, if it will be used for a class, the starting day of class and any days with tests.

### Hub Authentication
Hub auth type
: What kind of authentication service will be used for this community.
  This boils down to what kind of "log-in username" users wish to use on the hub.
  Currently, the two options are **GitHub handles** (e.g., `@mygithubhandle`) or Google OAuth usernames (e.g., `myname@2i2c.org`).
  You must choose **only one option**.
Hub administrators
: These are user accounts with **administrator access** to the hub.
  They will be able to create new users (including administrator users), view and debug user sessions, and shut down user sessions.
  See [the Hub Administrator section](https://pilot.2i2c.org/en/latest/) of the Hubs Pilot documentation for more information.

### Deployment information

Hub ID
: The unique ID used to identify this hub.
  The Community Representative should provide a URL-friendly community identifier (e.g. `my-university`).
Hub Cluster
: The cloud cluster where this hub will be run.
  For example, `pilot` or `cloudbank`.
Hub Template
: The configuration template that defines the basic infrastructure setup for the hub.
  There are two options:

  1. `basehub`: a basic JupyterHub with a fairly standard setup.
  2. `daskhub`: a JupyterHub with a Dask Gateway enabled for scalable computing.

### Hub Customization

Hub logo
: A URL to an image that will be used on the hub's landing page. (optional)
Hub logo URL
: A URL that the hub's logo will point to when users click on it on the landing page (optional)
User image registry service
: The image registry service used for this hub's user image, if a custom user image is desired.
  For example, a [quay.io registry image](https://quay.io/).
  See [](customize/custom-image) for more information.
User image
: A name and tag for a user image, pointing to the registry in the field above.  

## Cloud provider-specific information

The following sections contain information that is unique to each cloud provider.
Follow these guides in addition to the more general instructions above.

```{toctree}
add-aws-hub.md
```
