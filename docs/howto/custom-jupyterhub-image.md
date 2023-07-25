# Modify our custom JupyterHub image

The 2i2c hubs use a custom `hub` image that is defined in the [helm-charts directory of the infrastructure repository](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/images/hub).

## The `hub` image

This custom hub image is built on top of the [jupyterhub/k8s-hub](https://hub.docker.com/r/jupyterhub/k8s-hub) Docker image and configured based on the needs of 2i2c hubs.
This allows adding and configuring other packages like the [jupyterhub-configurator](https://github.com/yuvipanda/jupyterhub-configurator) or using specific versions of the spawner and authenticator.
More information about this custom image can be found in the [Dockerfile](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub/Dockerfile) itself.


## The `hub-experimental` image

In addition to the `hub` image, there is also a `hub-experimental` image, that is defined in the [helm-charts directory of the infrastructure repository](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/images/hub-experimental).

This `hub-experimental` image is very similar to the hub image, but its primary goal is to be used to test changes like new packages, newer package versions, or even unreleased or unmerged versions of them. It can be used to deploy such change just to one or a few specific communities, without having to worry about the instabilities it can generate for other communities.

```{note}
Both the 2i2c custom `hub` and the `hub-experimental` images live at [Quay.io](https://quay.io/organization/2i2c).
```

## When to roll out the changes in `hub-experimental` to `hub`

```{important}
Our current policy states that a change in `hub-experimental` must be rolled out into `hub`, **within  4 weeks**, otherwise it should be removed. Any issues identified within these 4 weeks, must be fixed it until it's good enough to deploy to all hubs.
```

The workflow is the following:
```{mermaid}
flowchart TD
  build_hub_experimental[Build a new `hub-experimental` image fa:fa-camera-retro]-->configure_hub_with_experiment[Configure the hub of at least one community to use the new image]
  configure_hub_with_experiment-->deploy_hub[fa:fa-rocket Deploy]
  -- Watch for one week to see how it goes! ---
  deploy_hub --> condition{{Runs for one week without needing any fixes?}}
  condition -- Yes --- roll_out[Roll out changes from `hub-experimental` into the `hub` image]
  condition -- No --- fix[Fix issues fa:fa-ban]
  fix --> condition
  roll_out --> deploy_everywhere[Deploy hub image everywhere fa:fa-rocket]
  -- More testing for hubs that are configured differently ---
  deploy_everywhere --> end_condition[`hub-experimental` image is the same as `hub` fa:fa-exclamation]
```

## How to install an unreleased version of a package in the `hub-experimental` image

To install an unreleased package, we will need to install directly from GitHub and not from PyPI:

1. Identify the package and commit you wish to install into the hub image. Example:

   ```bash
   https://github.com/jupyterhub/kubespawner@def501f1d60b8e5629745acb0bcc45b151b1decc
   ```

2. Update the [requirements.txt](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub-experimental/requirements.txt)) file to add this package and commit, prefixed by a `git+` on a new row. Example:

   ```bash
   git+https://github.com/jupyterhub/kubespawner@def501f1d60b8e5629745acb0bcc45b151b1decc
   ```

3. Commit the changes

   ```bash
   git add helm-charts/images/hub/Dockerfile
   git commit
   ```

   ```{note}
   The commit SHA with be used to generate the image tag.
   ```

## How to build and push a new version of the hub image (`hub` or `hub-experimental`)

Rebuild the Docker image and push it to the [Quay.io registry](https://quay.io/repository/2i2c/pilot-hub)
 
- Your `@2i2c` address should give you access to push to the Quay.io registry where the hub image lives, but make sure you are logged into quay.io container registry with the right credentials and these creds are configured to have access to <https://quay.io/repository/2i2c/pilot-hub>.
  Please contact someone at 2i2c for access if this is not the case.

  ```bash
  docker login quay.io
  ```

  ```{seealso}
  Checkout the [Getting Started with Quay.io](https://docs.quay.io/solution/getting-started.html) docs for more info.
  ```

- Make sure you have [jupyterhub/chartpress](https://github.com/jupyterhub/chartpress) installed.

  ```bash
  pip install chartpress
  ```

  This package is also listed under `dev-requirements.txt`, so it should be present if you've installed the dev dependencies.

- Make sure you are in the `helm-charts` directory, where the `chartpress.yaml` is located:

  ```bash
  cd ./helm-charts
  ```

- Run chartpress to build the image, push it to the registry and update the basehub helm chart to use the updated image tag

  ```bash
  chartpress --push
  ```

  ````{note}
  If you are on macOs with M1, you need to run chartpress with [docker buildx](https://docs.docker.com/build/buildx/) under the hood and specify which platform to use, i.e. `amd64`[^1].

  ```
  chartpress --push --builder docker-buildx --platform linux/amd64
  ```
  ````

- **If building and pushing the `hub` image**, then commit the changes made by `chartpress` to `helm-charts/basehub/values.yaml`, but discard the changes made to `helm-charts/basehub/Chart.yaml` as the last may cause problems with the `daskhub` dependency mechanism.

  ```bash
  git add helm-charts/basehub/values.yaml
  git commit
  ```

- **If building and pushing the `hub-experimental` image**, then discard the changes to both `helm-charts/basehub/values.yaml` and `helm-charts/basehub/Chart.yaml`, because we only want to deploy this image to particular hubs

## How to configure a hub to use the new `hub-experimental` image

You will need to put a config similar to the one below in your hub configuration file:

```
hub:
  image:
    name: quay.io/2i2c/experimental-hub
    tag: "0.0.1-0.dev.git.6406.hc1091b1c"
```

```{important}
The image tag of the of the [jupyterhub/k8s-hub](https://hub.docker.com/r/jupyterhub/k8s-hub) [in the Dockerfile](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub/Dockerfile#L9) must match the dependent JupyterHub Helm chart's version as declared in [basehub/Chart.yaml](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/Chart.yaml#L14).
```

[^1]: <https://cloudolife.com/2022/03/05/Infrastructure-as-Code-IaC/Container/Docker/Docker-buildx-support-multiple-architectures-images/>