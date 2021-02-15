# Cluster configuration

Information about how to customize and configure each of the cluster (or individual hubs).

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

## Hub templates
The hubs are configured and deployed using *hub templates*. Because each hub
type can be described by a template, with its own deployment chart, a hierarchy
of hub types can be built and this makes development and usage easier.

Currently there are two hub templates available:
- the `base-hub` template
- the `ephemeral-hub` template

For example, the **ephemeral hub** is a special kind of hub that is built using the *ephemeral-hub template*
and has the following features:

- Temporary, transient binder-style hub
- No authentication
- Resource limitations:
  * memory / CPU limits
  * maximum number of concurrent user servers
- More aggressive culling
- No persistent storage
- No home page template


The graphic below, shows the relationship between the hub templates and the other
config files and how they are merged together when deploying a JupyterHub.

```{figure} images/config-flow.png
```

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

## Adding additional domains to a hub

Existing pilot-hubs in the two 2i2c-managed clusters, have a subdomain created and assingned to them on creation,
that respects the following naming convention, based on which domain name and cluster they are part of:

- `<name-of-the-hub>.pilot.2i2c.cloud` - for the ones in the 2i2c cluster and *pilot.2i2c.cloud* domain
- `<name-of-the-hub>.cloudbank.2i2c.cloud` - for the ones in the cloudbank cluster and *cloudbank.2i2c.cloud* domain

But other domains can be easily linked to the same hub in a cluster if needed.

Assuming there is a hub named `foo` in the `2i2c` cluster and we want to add the `foo.edu` domain to it, one would:

1. **Point the `foo.edu` domain to the right cluster.**

    Create a [CNAME](https://en.wikipedia.org/wiki/CNAME_record) entry from the new domain, `foo.edu`, that points to the
    existing `foo.pilot.2i2c.cloud`, where the `foo` hub already runs.

    This will map the new domain name, `foo.edu`, to the default one `foo.pilot.2i2c.cloud` - *the canonical name* and will
    make sure `foo.edu` points to the right cluster, no matter which IP address the cluster has.

2. **Point the `foo.edu` domain to the right hub.**

    Since all the hubs in a cluster are running at the same IP address, but are available at different subdomains,
    we also need a way to specify which hub in this cluster we want the new domain and subsequent requests to point to.

    For this to happen we need to add the new domain as an ingress domain for this hub using the `hubs.yaml` configuration file.
    This can be done by adding the new domain to the list in `hubs.<hub-name>.domain`:

      ```yaml
      - name: foo
        cluster: 2i2c
        domain:
          - foo.pilot.2i2c.cloud # default domain
          - foo.edu # additionl domain
        (...)
      ```

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