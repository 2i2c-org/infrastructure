# Modify our custom JupyterHub image

The 2i2c hubs use a custom hub image that is defined in the [helm-charts directory of the infrastructure repository](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/images/hub).

This custom hub image is built on top of the [jupyterhub/k8s-hub](https://hub.docker.com/r/jupyterhub/k8s-hub) Docker image and configured based on the needs of 2i2c hubs.
This allows adding and configuring other packages like the [jupyterhub-configurator](https://github.com/yuvipanda/jupyterhub-configurator) or using specific versions of the spawner and authenticator.
More information about this custom image can be found in the [Dockerfile](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub/Dockerfile) itself.

The 2i2c custom hub image is lives at [Quay.io](https://quay.io/repository/2i2c/pilot-hub).

## Updating the hub image

When this hub image needs to be updated, the steps to take are:

1. Update the [Dockerfile](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub/Dockerfile) with any changes wanted

2. Commit the changes

   ```bash
   git add helm-charts/images/hub/Dockerfile
   git commit
   ```

   ```{note}
   The commit SHA with be used to generate the image tag.
   ```

3. Rebuild the Docker image and push it to the [Quay.io registry](https://quay.io/repository/2i2c/pilot-hub)
 
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

   - Commit the changes made by `chartpress` to `helm-charts/basehub/values.yaml`, but discard the changes made to `helm-charts/basehub/Chart.yaml` as the last may cause problems with the `daskhub` dependency mechanism.

     ```bash
     git add helm-charts/basehub/values.yaml
     git commit
     ```

```{note}
The image tag of the of the [jupyterhub/k8s-hub](https://hub.docker.com/r/jupyterhub/k8s-hub) [in the Dockerfile](https://github.com/2i2c-org/infrastructure/blob/HEAD/helm-charts/images/hub/Dockerfile#L9) must match the dependent JupyterHub Helm chart's version as declared in [basehub/Chart.yaml](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/basehub/Chart.yaml#L14).
```

[^1]: <https://cloudolife.com/2022/03/05/Infrastructure-as-Code-IaC/Container/Docker/Docker-buildx-support-multiple-architectures-images/>
