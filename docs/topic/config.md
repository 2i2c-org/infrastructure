# Configuration Structure

This page describes the basic structure of our hub configuration.

## Inheritance of configuration

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | [`helm-charts/basehub/Chart.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/Chart.yaml) lists the z2jh version. Most of our configuration is directly from upstream |
| [`helm-charts/basehub/values.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml) | 2i2c engineers | Common to all hubs run from this repo |
| [Deployment script](https://github.com/2i2c-org/infrastructure/tree/HEAD/deployer) | 2i2c engineers | Programmatic overrides for each type of hub, particularly around Auth0 integration and home page customization |
| [`config/clusters` (previously `hubs.yaml`)](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters) | 2i2c engineers | There is one folder per cluster, and each cluster can have multiple hubs deployed defined by a `<hub_name>.values.yaml` file in the same folder. There is also clster-wide config stored in a `cluster.yaml` in each cluster directory. [`config/clusters/schema.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/schema.yaml) contains documentation and validation information for fields in this set of configuration. |
| [Configurator schema defaults](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L143) | 2i2c engineers | **If** there is a default set in the schema for available options in the configurator, it will always override the config elsewhere in our YAML files |
| Configurator | Hub admins | If hub admins 'unset' a value, it should go to what's configured via our yaml files|

## Location of common configuration

Finding out what the value for a particular piece of configuration is can be
a bit tricky, since there are many places to look at. Here, we'll look at some common
pieces of config people want to know values for, and where you can find them.

### Memory limits

The default memory limit and guarantee for all users across all our hubs is set
in [`helm-charts/basehub/values.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L104),
under `jupyterhub.singleuser.memory`. This is sometimes overriden on a per-hub
basis in the config for the hub under [`config/clusters`](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters)

### 2i2c staff lists

The 2i2c team keeps a central list of staff usernames that it automatically adds as administrators to each of the hubs that we deploy.

When a hub is deployed, some custom code is run as part of `jupyterhub_config.py` and the usernames corresponding to the correct staff list are added to the hub's Admin and Allowed users.

You can find the list of staff usernames in [the `basehub` helm chart](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L52) along with the [custom code](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L392) used to inject them.
