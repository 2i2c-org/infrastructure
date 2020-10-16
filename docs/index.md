# 2i2c Pilot Hubs Infrastructure

This is documentation for the 2i2c Pilot Hubs deployment infrastructure. The goal of this stack is to automatically deploy JupyterHubs in the cloud from a single `hubs.yaml` configuration file.

All hub configuration is in `hubs.yaml`. You can add a new hub by adding
an entry there, and pushing that to github.

## How we plan to use this repository

Currently, most user-facing documentation for the Hubs Pilot is at [2i2c.org/pilot](https://2i2c.org/pilot/). We'll use the following repositories for managing users and maintenance of these hubs:

- [github.com/2i2c-org/pilot](https://github.com/2i2c-org/pilot) - point-of-contact with users. User documentation. Questions, requests, problems, etc.
- [github.com/2i2c-org/pilot-hubs](https://github.com/2i2c-org/pilot-hubs) - Hub deployment information, issues for maintenance and technical enhancements on the hubs.

We've asked users to submit any questions, problems, requests, etc as issues via [github.com/2i2c-org/pilot](https://github.com/2i2c-org/pilot) using issue templates. **Hub operators** should triage these issues, and surface any that require ongoing attention as issues in the [github.com/2i2c-org/pilot-hubs](https://github.com/2i2c-org/pilot-hubs) repository. This includes technical problems that need fixes, as well as requests such as environment updates.

2i2c Hub Operators as well as Hub Architects shall use this repository to perform hub updates and maintenance in order to resolve these issues. They'll also use this repository to create new hubs for communities that have reached out via [https://2i2c.org/pilot](2i2c.org/pilot).

## Cluster configuration reference

At the top level of `hubs.yaml` is a list of **clusters**. Each cluster is a cloud deployment (for example, a Google project) that can have one or more hubs deployed inside it.

Clusters have some basic configurability:

`name`
: A string that uniquely identifies this cluster

`image_repo`
: The base **user image** that all hubs will use in this cluster.

`provider`
: The cloud provider for this cluster (e.g. `gcp`).

## Hub configuration reference

`clusters.hubs:` is a list of hubs to be deployed in each cluster.
Each hub is a dictionary that can consist of the following keys:

`name`
: A string that uniquely identifies this hub

`cluster`
: The cluster where this hub will be deployed.

`domain`
: Domain this hub should be available at. Currently, must be a subdomain
  of a domain that has been pre-configured to point to our cluster. Currently,
  that is `.<clustername>.2i2c.cloud`

`auth0`
: We use [auth0](https://auth0.com/) for authentication, and it supports
  many [connections](https://auth0.com/docs/identityproviders). Currently,
  only `connector` property is supported - see section on *Authentication*
  for more information.

`config.jupyterhub`
: Any arbitrary [zero to jupyterhub](https://z2jh.jupyter.org) configuration
  can be passed here. Most common is auth setup, memory / CPU restrictions,
  and max number of active users. See [](config-jupyterhub) for more info.

(config-jupyterhub)=
## Configuring each JupyterHub

Each JupyterHub can use its own configuration via the `hubs.yaml` file. This configuration exists under `config.jupyterhub`.
This should be a valid [Zero to JupyterHub](https://z2jh.jupyter.org) configuration. For example, to set a custom memory limit for a hub, you would use:

```yaml
config:
   jupyterhub:
    singleuser:
       memory:
          limit: 1G
```

Here are a few reference pages for JupyterHub Kubernetes configuration:

- {ref}`z2jh:user-environment`
- {ref}`z2jh:user-resources`

## Authentication

[auth0](https://auth0.com) provides authentication for all hubs here. It can
be configured with many different [connections](https://auth0.com/docs/identityproviders)
that users can authenticate with - such as Google, GitHub, etc.

So we want to manage authentication by:

1. Explicitly listing the type of connection we want for this hub, via
   `auth0.connection`. Currently common ones are `google-oauth2` for Google &
   `github` for GitHub. *Users* of the hub will use this method to log in to
   the hub.

   You can set the auth0 connector for a hub with:

   ```yaml
   auth0:
      connection: google-oauth2
   ```

   Theoretically, every provider in [this list](https://auth0.com/docs/connections/identity-providers-social)
   is supported. However, we've currently only tested this with Google
   (`google-oauth2`) and GitHub (`github`)

2. Explicitly list *admin users* for a given hub. These admin users will be the
   only ones allowed to log in to begin with. They can use the JupyterHub
   admin interface (available from their hub control panel) to explicitly allow
   more users into the hub. This way, we don't need to be involved in explicitly
   allowing users into hubs.

   In the admin interface, admin users can add users via a username appropriate
   for the auth connector used. For GitHub, it's the username. For Google Auth,
   it's the email address.

   You can set the admin interfaces for a hub like this:

   ```yaml
   config:
     jupyterhub:
       auth:
         # will be renamed allowedlist in future JupyterHub
         whitelist:
           users:
             # WARNING: THESE USER LISTS MUST MATCH (for now)
             - user1@gmail.com
             - user2@gmail.com
         admin:
           users:
             # WARNING: THESE USER LISTS MUST MATCH (for now)
             - user1@gmail.com
             - user2@gmail.com
   ```

:::{admonition} Switching auth
Switching authentication for a pre-existing hub will simply create new usernames. Any pre-existing users will no longer be able to access their accounts (although administrators will be able to do so). If you have pre-existing users and want to switch the hub authentication, rename the users to the new auth pattern (e.g. convert github handles to emails).
:::

## Default options

Part of being 'low touch' is to provide default options that we think might
work for most people. These are specified in `hub/values.yaml` in the repository.
We list some common ones here.

1. **Memory Limit** of 1G per student, with a guarantee of 256M. This means that
   everyone will be *guaranteed* 256M of memory, and most likely will have access
   to 1G of memory. But they can't use more than 1G of memory - their kernels and
   processes will die if they use more than this.

## Updating environment

The user environments is specified via a `Dockerfile`, under `images/user` in
the git repository. Currently there is no automated image building - so you will
have to manually build & push it after making a change.

1. Install pre-requisites:

   a. Docker
   b. A Python virtual environment. Install `requirements.txt` into it.
   c. The `gcloud` tool, authenticated to the `two-eye-two-see` project.
      You need to run `gcloud auth configure-docker us-central1-docker.pkg.dev`
      once as well.

2. Make the changes you need to make to the environment, and git commit it.

3. Run `python3 deploy.py build`. This will build the image and push it to
   registry. It will tell you what the generated image tag is.

4. Update `jupyterhub.singleuser.image.tag` in `hub/values.yaml` with this tag.

5. Make a commit, make a PR and merge to master! This will deploy all the hubs
   with the new image

## Configuring the hub login page

Each Hub deployed in a cluster has a collection of metadata about who it is deployed for, and who is responsible for running it. This is used to generate the **log-in page** for each hub and tailor it for the community.

For an example, see [the log-in page of the staging hub](https://staging.pilot.2i2c.cloud/hub/login).

The log-in pages are built with [the base template at this repository](https://github.com/2i2c-org/pilot-homepage). Values are inserted into each template based on each hub configuration.

You may customize the configuration for a hub's homepage at `config.jupyterhub.homepage.templateVars`. Changing these values for a hub will make that hub's landing page update automatically. We recommend [using the `hubs.yaml` file as a reference](https://github.com/2i2c-org/pilot-hubs/blob/master/hubs.yaml). Copy the configuration from another hub, and then modify the contents to fit the new hub that is being configured.

## Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.
2. **Backup the home directory contents**. Especially if we think that users will want this information in the future (or if we plan to re-deploy a hub elsewhere).
3. **Delete the Helm namespace**. Run `helm -n <hub-name> delete <hub-name>`.
4. **Delete our Authentication entry**. If the hub hasn't been recreated anywhere, remove the entry from `auth0.com`
