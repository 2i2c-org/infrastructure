# Where does config come from?

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | `hub-templates/base-hub/Chart.yaml` lists the z2jh version. Most of our configuration is directly from upstream | 
| `hub-templates/base-hub/values.yaml` | 2i2c engineers | Common to all hubs run from this repo |
| `deploy.py` | 2i2c engineers | Programmatic overrides for each type of hub, particularly around Auth0 integration |
| `hubs.yaml` | 2i2c engineers | Specific to each hub |
| [Configurator schema defaults](https://github.com/2i2c-org/pilot-hubs/blob/6248cf84f2e888cb89bbb75e591e9507dabf6f3c/hub-templates/base-hub/values.yaml#L125) | 2i2c engineers | **If** there is a default set in the schema for available options in the configurator, it will always override the config elsewhere in our YAML files | 
| Configurator | Hub admins | If hub admins 'unset' a value, it should go to what's configured via our yaml files|
