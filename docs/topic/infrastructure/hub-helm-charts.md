(hub-helm-charts)=
# Hub helm charts

```{warning}
The `daskhub` helm chart has now been deprecated and `dask-gateway` is now a conditional dependency of the `basehub` chart. It shouldn't be used for new hub deployments.

However there are still existing hub configuration that uses a chart called `daskhub`. This is just for backward compatibility in order to not disrupt existing deployments by causing hubs reinstallations and should not be replicated going further.
```
The hubs are configured and deployed using [*locally defined helm charts*](https://helm.sh/docs/topics/chart_repository/#create-a-chart-repository). Because each hub
type can be described by a helm chart, a hierarchy
of hub types can be built and this makes development and usage easier.

The graphic below, shows the relationship between the hub helm charts and the other
config files and how they are merged together when deploying a hub.

```{figure} ../../images/config-flow.png
```
% The editable version of the diagram is here: https://docs.google.com/presentation/d/1WZKTe5TSDU-5zA4NnNEPsKfgjaBzUqMgdPLTnz-Yb94/edit?usp=sharing

Currently there are two hub helm charts available:
- `basehub`

  The **basehub helm chart** is the chart that the other hub helm charts "inherit" and configure.
  It provides a base JupyterHub, user storage and culling configuration that satisfies most of the infrastructure usage requirements.

- `daskhub`

  The **daskhub helm chart** helps deploying dask-enabled hubs.
    - Installs [dask-gateway](https://gateway.dask.org/)
    - Defaults to using a [PANGEO image](https://pangeo-data.github.io/pangeo-stacks/)
    - Enables outgoing SSH

## Use the helm charts to deploy a new hub

To deploy a new hub, you only need to add a new `*.values.yaml` file to the appropriate cluster folder file under `config/clusters`, and add a new entry to the `hubs` key in that cluster's `cluster.yaml` file.
This configuration file allows specifying options like the type of helm chart to use for the hub being added,
the hub domain, how the JupyterHub landing page will look like and authentication preferences.

The helm charts are structured in a **hierarchical** model.
The [jupyterhub helm chart](https://jupyterhub.github.io/helm-chart/) is a subchart of the basehub chart and
the basehub chart along with the [dask-gateway](https://helm.dask.org) one are
subcharts of the daskhub.

**Visual of the helm-chart hierarchy:**
```{figure} ../../images/helm-charts-hierarchy.png
```
% The editable version of the diagram is here: https://docs.google.com/presentation/d/1KMyrTd3wdR715tPGuzIHkHqScXBlLpeiksIM2x7EI0g/edit?usp=sharing

This hierarchy is the reason why when adding a new hub using the `daskhub`
specific configuration in a `*.values.yaml` file needs to be nested under a `basehub` key, indicating that we are overriding configuration
from the *basehub/jupyterhub* parent chart.

Read more about subcharts and how to configure them in the [Helm docs](https://helm.sh/docs/chart_template_guide/subcharts_and_globals/#overriding-values-from-a-parent-chart).
