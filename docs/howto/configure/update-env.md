# Update environment

The default user environment is specified in its own GitHub repository, located
at https://github.com/2i2c-org/pilot-hubs-image.

The image is built and pushed using [jupyterhub/repo2docker-action](https://github.com/jupyterhub/repo2docker-action)
to the [pilot-hubs-image quay.io](https://quay.io/repository/2i2c/pilot-hubs-image).
registry

To update this environment:

1. Make the changes you need to make to the environment, by editing the files in
   the [pilot-hubs-image repository](https://github.com/2i2c-org/pilot-hubs-image)
   and open a pull request. This will also provide you the ability to test your
   changes on Binder to make sure everything works as expected.
2. Once the PR is merged or a commit to the `main` branch happens, the new image will be pushed
   to the registry.
3. Get the latest tag from the [tags section](https://quay.io/repository/2i2c/pilot-hubs-image?tab=tags) in quay.io
4. Update `jupyterhub.singleuser.image.tag` in `hub-templates/basehub/values.yaml` with this tag.
