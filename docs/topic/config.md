# Configuration Structure

This page describes the basic structure of our hub configuration.

## Inheritance of configuration

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | [`helm-charts/basehub/Chart.yaml`](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/Chart.yaml) lists the z2jh version. Most of our configuration is directly from upstream |
| [`helm-charts/basehub/values.yaml`](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/values.yaml) | 2i2c engineers | Common to all hubs run from this repo |
| [Deployment script](https://github.com/2i2c-org/infrastructure/blob/master/deployer) | 2i2c engineers | Programmatic overrides for each type of hub, particularly around Auth0 integration and home page customization |
| [`config/hubs` (previously `hubs.yaml`)](https://github.com/2i2c-org/infrastructure/blob/master/config/hubs) | 2i2c engineers | Specific to each hub. There is one YAML file per cluster, and each cluster can have multiple hubs deployed.  [`config/hubs/schema.yaml`](https://github.com/2i2c-org/infrastructure/blob/master/config/hubs/schema.yaml) contains documentation and validation information for fields in this set of configuration. |
| [Configurator schema defaults](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/values.yaml#L143) | 2i2c engineers | **If** there is a default set in the schema for available options in the configurator, it will always override the config elsewhere in our YAML files |
| Configurator | Hub admins | If hub admins 'unset' a value, it should go to what's configured via our yaml files|

## Location of common configuration

Finding out what the value for a particular piece of configuration is can be
a bit tricky, since there are many places to look at. Here, we'll look at some common
pieces of config people want to know values for, and where you can find them.

### Memory limits

The default memory limit and guarantee for all users across all our hubs is set
in [`helm-charts/basehub/values.yaml`](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/values.yaml#L104),
under `jupyterhub.singleuser.memory`. This is sometimes overriden on a per-hub
basis in the config for the hub under [`config/hubs`](https://github.com/2i2c-org/infrastructure/blob/master/config/hubs)

### 2i2c staff lists

The 2i2c team keeps a central list of staff usernames that it automatically adds as administrators to each of the hubs that we deploy.
When a new hub is created, we use one of these two placeholders to add 2i2c staff to the hub:

- `<staff_github_ids>` - If the hub uses GitHub authentication
- `<staff_google_ids>` - If the hub uses Google OAuth authentication

When a hub is deployed, these placeholders are removed, and the usernames corresponding to the correct staff list are added to the hub's Admin and Allowed users.

You can find the list of staff usernames at [`config/hubs/staff.yaml`](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs/staff.yaml).
