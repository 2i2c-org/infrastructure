# Hub configuration reference

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
  and max number of active users. See [](../howto/configure/hub-config.md) for more info.