(config)=
# Configuration structure

This page describes the basic structure of our hub configuration.

## Inheritance of configuration

These configuration sources are merged in the following order to produce config
for each hub.

| Source | Maintainer | Notes |
| - | - | - |
| Upstream defaults from z2jh | z2jh maintainers | [`helm-charts/basehub/Chart.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/Chart.yaml) lists the z2jh version. Most of our configuration is directly from upstream |
| [`helm-charts/basehub/values.yaml`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml) | 2i2c engineers | Common to all hubs run from this repo |
| [`config/clusters` (previously `hubs.yaml`)](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters) | 2i2c engineers | There is one folder per cluster, and each cluster can have multiple hubs deployed defined by a `<hub_name>.values.yaml` file in the same folder. There is also cluster-wide config stored in a `cluster.yaml` in each cluster directory. [`config/clusters/schema.yaml`](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/cluster.schema.yaml) contains documentation and validation information for fields in this set of configuration. |
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

(config:structure)=
## Configuration structure

We have a [`config/clusters` directory](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters) which contains folders that each contain configuration files describing a single cluster and the JupyterHubs running on that cluster.
See the [2i2c cluster folder](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/2i2c) for an example.

Each cluster folder must contain **one** (1) of the following files:

`cluster.yaml`
: This file contains cluster-wide configuration specific to the cluster, including: the provider the cluster is hosted on, the path to a credentials file that grants programmatic access to the cluster, a list of JupyterHubs running on the cluster, and the paths to all configuration files that individually describes those JupyterHubs.
We follow the convention that the `name` field defined in this file should match the name of the cluster folder it resides within.

Deployer credentials
: A `sops`-encrypted YAML or JSON file that can provide programmatic access to a cluster by updating a [`KUBECONFIG` file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/).
These credential files have the naming convention `enc-deployer-credentials.secret.{{ json | yaml }}` when ecrypted.

(Optional) Grafana API Token
: This token allows us to programmatically create a range of useful dashboards in a cluster's grafana deployment, allowing us to inspect and track the usage of all the JupyterHubs deployed to that cluster.
See the [](grafana-dashboards) documentation for more information on how this token is used.
These token files have the naming convention `enc-grafana-token.secret.yaml` when encrypted.

Additionally, the cluster folder can contain any number of helm chart values files to describe any individual JupyterHub running on the cluster.
These files follow the naming convention `<hub-name>.values.yaml` where `<hub-name>` matches a `hubs.[*].name` entry in the `cluster.yaml` file, and the path to the values file is listed under the associated `helm_chart_values_files` key _relative to_ the `cluster.yaml` file.
See the config for the [staging hub on the 2i2c cluster](https://github.com/2i2c-org/infrastructure/blob/HEAD/config/clusters/2i2c/cluster.yaml#L19-L31) for an example.

```{admonition} Secret helm chart values files

A hub's helm chart values file can be encrypted as well, following the naming convention `enc-<hub-name>.secret.values.yaml`
```

Where we run dedicated clusters that only host a `staging` and `prod` hub, we aggregate all helm chart values shared by each hub into a `common.values.yaml` file, and then describe the helm chart values specific to either `staging` or `prod` with a `staging.values.yaml` or `prod.values.yaml` file respectively.
See the [Pangeo config](https://github.com/2i2c-org/infrastructure/blob/HEAD/config/clusters/pangeo-hubs/cluster.yaml) for an example.
This may lead to cases where two hubs on the same cluster use the same config for the `staging` and `prod` hubs, see the [Carbon Plan config](https://github.com/2i2c-org/infrastructure/blob/HEAD/config/clusters/carbonplan/cluster.yaml) as an example.

### Conventions for our configuration structure

When designing our configuration structure, we apply the following conventions.

1. The `cluster.yaml` file of any given cluster is the only file that our deployment infrastructure should have to calculate the filepath for.
   Other files required to deploy a given hub onto the given cluster should be explicitly defined _relative_ to the position of the `cluster.yaml` file.
2. We should move configuration files around as needed to fit convention 1 in the most logical manner without traversing a lot of directories up/down where possible.
   We want to strictly avoid (but not enforce) overly-complicated relative filepaths, such as:

   ```yaml
   helm_chart_values_files:
     - this/is/a/directory/file.values.yaml
     - ../../../../../who/knows/where/this/is/file.values.yaml
   ```

   While the first option could be considered reasonable since the filepath is explicit, the second one can become confusing due to the repetition of the `..` operator.
   If we find ourselves writing complicated relative filepaths like this, we should reassess and move that config to somewhere more logical.
3. In the spirit of convention 2, we should not house our secrets under a specific folder and mimic the structure of `config/clusters` under it.
   Instead, we define all config for a cluster, encrypted or not, into the same place.
   We then use filenames to track if a file should be encrypted and whether it is currently encrypted or not.
   See [](secrets:top) for more information on this.
