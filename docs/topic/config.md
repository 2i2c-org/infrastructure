# Configuration Structure

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | [`hub-templates/basehub/Chart.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/hub-templates/basehub/Chart.yaml) lists the z2jh version. Most of our configuration is directly from upstream | 
| [`hub-templates/basehub/values.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/hub-templates/basehub/values.yaml) | 2i2c engineers | Common to all hubs run from this repo |
| [Deployment script](https://github.com/2i2c-org/pilot-hubs/blob/master/deployer) | 2i2c engineers | Programmatic overrides for each type of hub, particularly around Auth0 integration and home page customization |
| [`config/hubs` (previously `hubs.yaml`)](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs) | 2i2c engineers | Specific to each hub. There is one YAML file per cluster, and each cluster can have multiple hubs deployed.  [`config/hubs/schema.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs/schema.yaml) contains documentation and validation information for fields in this set of configuration. |
| [Configurator schema defaults](https://github.com/2i2c-org/pilot-hubs/blob/c1d06be1eed2d748a4d39e4cba76436cffe89fb2/hub-templates/basehub/values.yaml#L143) | 2i2c engineers | **If** there is a default set in the schema for available options in the configurator, it will always override the config elsewhere in our YAML files | 
| Configurator | Hub admins | If hub admins 'unset' a value, it should go to what's configured via our yaml files|

## Location of common configuration

Finding out what the value for a particular piece of configuration is can be
a bit tricky, since there are many places to look at. Here, we'll look at some common
pieces of config people want to know values for, and where you can find them.

### Memory limits

The default memory limit and guarantee for all users across all our hubs is set
in [`hub-templates/basehub/values.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/hub-templates/basehub/values.yaml#L104),
under `jupyterhub.singleuser.memory`. This is sometimes overriden on a per-hub
basis in the config for the hub under [`config/hubs`](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs)