# Hub templates
The hubs are configured and deployed using *hub templates*. Because each hub
type can be described by a template, with its own deployment chart, a hierarchy
of hub types can be built and this makes development and usage easier.

The graphic below, shows the relationship between the hub templates and the other
config files and how they are merged together when deploying a pilot hub.

```{figure} ../images/config-flow.png
```
% The editable version of the diagram is here: https://docs.google.com/presentation/d/1WZKTe5TSDU-5zA4NnNEPsKfgjaBzUqMgdPLTnz-Yb94/edit?usp=sharing

Currently there are three hub templates available:
- `base-hub`

  The **base-hub template** is the template that the other templates "inherit" and configure.
  It provides a base JupyterHub, user storage and culling configuration that satisfies most of the
  pilot hubs usage requirements.

- `daskhub`

  The **daskhub template** helps deploying dask-enabled hubs.
    - Installs [dask-gateway](https://gateway.dask.org/)
    - Defaults to using a [PANGEO image](https://pangeo-data.github.io/pangeo-stacks/)
    - Enables outgoing SSH

## Use the templates to deploy a new hub

To deploy a new hub, you only need to add it to the appropriate configuration file under `config/hubs`.
This configuration file allows specifying options like the type of template to use for the hub being added,
the hub domain, how the JupyterHub landing page will look like and authentication preferences.

Because the templates are structured in a **hierarchical** model, so are their helm charts.
The [jupyterhub helm chart](https://jupyterhub.github.io/helm-chart/) is a subchart of the base-hub and
the base-hub chart along with the [dask-gateway](https://dask.org/dask-gateway-helm-repo/) one are
subcharts of the daskhub. 

**Visual of the helm-chart hierarchy:**
```{figure} ../images/helm-charts-hierarchy.png
```
% The editable version of the diagram is here: https://docs.google.com/presentation/d/1KMyrTd3wdR715tPGuzIHkHqScXBlLpeiksIM2x7EI0g/edit?usp=sharing

This hierachy is the reason why when adding a new hub using the `daskhub` 
specific configuration under `config/hubs` needs to be nested under a `base-hub` key, indicating that we are overriding configuration
from the *base-hub/jupyterhub* parent chart.

Read more about subcharts and how to configure them in the [Helm docs](https://helm.sh/docs/chart_template_guide/subcharts_and_globals/#overriding-values-from-a-parent-chart).