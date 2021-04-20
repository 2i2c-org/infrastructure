# Where does config come from?

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | [`hub-templates/base-hub/Chart.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/hub-templates/base-hub/Chart.yaml) lists the z2jh version. Most of our configuration is directly from upstream | 
| [`hub-templates/base-hub/values.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/hub-templates/base-hub/values.yaml) | 2i2c engineers | Common to all hubs run from this repo |
| [Deployment script](https://github.com/2i2c-org/pilot-hubs/blob/master/deploy) | 2i2c engineers | Programmatic overrides for each type of hub, particularly around Auth0 integration and home page customization |
| [Per-hub customization (previously `hubs.yaml`)](https://github.com/2i2c-org/pilot-hubs/blob/master/clusters) | 2i2c engineers | Specific to each hub. There is one YAML file per cluster, and each cluster can have multiple hubs deployed |
| [Configurator schema defaults](https://github.com/2i2c-org/pilot-hubs/blob/6248cf84f2e888cb89bbb75e591e9507dabf6f3c/hub-templates/base-hub/values.yaml#L125) | 2i2c engineers | **If** there is a default set in the schema for available options in the configurator, it will always override the config elsewhere in our YAML files | 
| Configurator | Hub admins | If hub admins 'unset' a value, it should go to what's configured via our yaml files|
