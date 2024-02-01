# Automatically bumping image tags and helm sub-chart versions

Throughout the `infrastructure` repo we have a few upstream dependencies.
This section will focus on the images our JupyterHubs use to define environments and services, the sub-charts our helm charts are built on top of, and the process we have for automatically keeping these up-to-date with upstream releases.

## Bumping image tags

To keep the tags of any images we use up-to-date with upstream container registries, we use this Action: [sgibson91/bump-jhub-image-action](https://github.com/sgibson91/bump-jhub-image-action) in the [`bump-image-tags.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/bump-image-tags.yaml).

This workflow runs as a matrix where one matrix job relates to one config file.
A config file might be a `*.values.yaml` file for a specific hub, or a `values.yaml` file for a helm chart.
But all it really needs to contain is valid YAML!

Two inputs are required for this Action:

1. The path to the config file as defined from the root of the repository, e.g., `helm-charts/basehub/values.yaml`
2. A variable called `images_info` which is a list of dictionaries containing information about the images we wish to bump in the given config file.
   By providing a list in this way, we can choose to include/exclude images in the given config from being bumped.

Each dictionary in the `images_info` list must have a `values_path` key whose value is a valid [JMESPath expression](https://jmespath.org) to the image we would like to bump.
The example below would bump the `singleuser` image.

```json
[{"values_path": ".singleuser.image"}]
```

Additionally, you can provide a `regexpr` key with a valid regular expression that will filter the tags available on the container registry.
This can be particularly useful if the image has different tags published, e.g., commit tags as well as date tags, etc.

```{admonition} More configuration options
Please see the [project README](https://github.com/sgibson91/bump-helm-deps-action#readme) for more information about configuring this Action.
```

When triggered, either on a schedule or by a workflow dispatch event, the Action will open a Pull Request for each item in the matrix, bumping the tags for the defined images in the defined config for each matrix job.

```{warning}
Currently this Action only works for images that are **publicly available** on either **Docker Hub** or **quay.io**.

- To contribute support for other container registries, see [this issue](https://github.com/sgibson91/bump-jhub-image-action/issues/73)
- To contribute support for authenticated calls to container registries, see [this issue](https://github.com/sgibson91/bump-jhub-image-action/issues/99)
```

## Bumping helm sub-chart versions

To keep the versions of sub-charts (charts our helm charts depend on) up-to-date with upstream releases, we use this Action: [sgibson91/bump-helm-deps-action](https://github.com/sgibson91/bump-helm-deps-action) in the [`bump-helm-versions.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/bump-helm-versions.yaml).

This workflow runs as a matrix where one matrix job relates to one of our helm charts, e.g., `basehub`.
A config file is where the dependencies for that helm chart are listed.
This is usually in a `Chart.yaml` file, but has historically also been a `requirements.yaml file`.
All it really needs to contain is valid YAML!

Two inputs are required for this Action:

1. The path to the config file as defined from the root of the repository, e.g., `helm-charts/basehub/Chart.yaml`
2. A variable called `chart_urls` which is a dictionary containing information about the sub-charts we wish to bump in the given config file.
   By providing a dictionary in this way, we can choose to include/exclude sub-charts in the given config from being bumped.

The `chart_urls` has the sub-charts we wish to bump as keys, and URLs where a list of published versions of those charts is available.
An example below would bump the JupyterHub subchart of the basehub helm chart.

```json
{"jupyterhub": "https://jupyterhub.github.io/helm-chart/index.yaml"}
```

Note that the URL is not the expected <https://jupyterhub.github.io/helm-chart/>.
This is so the Action can pass the file contents directly to a YAML parser, rather than having to scrape the rendered site's HTML.

```{admonition} More configuration options
Please see the [project README](https://github.com/sgibson91/bump-jhub-image-action#readme) for more information about configuring this Action.
```

When triggered, either on a schedule or by a workflow dispatch event, the Action will open a Pull Request for each item in the matrix, bumping the versions for the defined sub-charts in the defined config for each matrix job.

```{warning}
Currently this Action only works for sub-charts that have a YAML formatted index of versions published at a URL that either:

- contains `/gh-pages/`, or;
- ends with `index.yaml` (or `index.yml`).

Other sources for version lists, such as GitHub Releases or HTML sites, will need to have code added upstream as they are required.
```
