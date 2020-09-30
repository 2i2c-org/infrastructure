# Hubs via hubs.yaml

All hub configuration is in `hubs.yaml`. You can add a new hub by adding
an entry there, and pushing that to github.

## Hub configuration reference

Each hub is a dictionary that can consist of the following keys:

1. `name`

   A string that uniquely identifies this hub

2. `domain`

   Domain this hub should be available at. Currently, must be a subdomain
   of a domain that has been pre-configured to point to our cluster. Currently,
   that is `.pilot.2i2c.cloud`

3. `auth0`

    We use [auth0](https://auth0.com/) for authentication, and it supports
    many [connections](https://auth0.com/docs/identityproviders). Currently,
    only `connector` property is supported - see section on *Authentication*
    for more information.
    
4. `config`

    Any arbitrary [zero to jupyterhub](https://z2jh.jupyter.org) configuration
    can be passed here. Most common is auth setup, memory / CPU restrictions,
    and max number of active users.
    
    All zero to jupyterhub config needs to be under a `jupyterhub` key. For example,
    if you wanna set the memory limit for a hub, you would use:
    
    ```yaml
    config:
      jupyterhub:
        singleuser:
          memory:
            limit: 1G
    ```
    

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
   
   
## Default options

Part of being 'low touch' is to provide default options that we think might
work for most people. These are specified in `hub/values.yaml` in the repository.
We list some common ones here.

1. **Memory Limit** of 1G per student, with a guarantee of 256M. This means that
   everyone will be *guaranteed* 256M of memory, and most likely will have access
   to 1G of memory. But they can't use more than 1G of memory - their kernels and
   processes will die if they use more than this.
