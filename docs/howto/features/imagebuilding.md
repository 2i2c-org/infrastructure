# Make an imagebuilding hub

We can support users who want to build, push and launch user images, from open source GitHub repositories, similar with what [mybinder.org](https://mybinder.org) does, but from within their JupyterHubs

We call this an `imagebuilding` style hub and the primary features offered would be:

- **User authentication**
- **Persistent storage**
- **Server options** allowing:
  - pre-defined list of images to choose from
  - specifying another image, different from the ones in the pre-defined list
  - building and pushing an image to a registry from a GitHub repository

## Use the `dynamic-image-building-experiment` hub image

We will need to use `jupyterhub-fancy-profiles`, but this Python package isn't installed in the default image deployed with our hubs, so we should use the [`dynamic-image-building-experiment` hub image](https://github.com/2i2c-org/infrastructure/blob/main/helm-charts/images/hub/dynamic-image-building-requirements.txt) instead.

```yaml
jupyterhub:
  hub:
    image:
      name: quay.io/2i2c/dynamic-image-building-experiment
      tag: "0.0.1-0.dev.git.8663.h049aa2c2"
```

## Connect with `jupyterhub-fancy-profiles`

1. The [jupyterhub-fancy-profiles](https://github.com/yuvipanda/jupyterhub-fancy-profiles) project provides a user facing frontend for connecting the JupyterHub to the BinderHub service, allowing the users to build their own images similar with how they would on mybinder.org.

    ```yaml
    jupyterhub:
      hub:
        extraConfig:
          enable-fancy-profiles: |
            from jupyterhub_fancy_profiles import setup_ui
            setup_ui(c)
    ```

2. Since `jupyterhub-fancy-profiles` adds on to the [`profileList` feature of `KubeSpawner`](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html#kubespawner.KubeSpawner.profile_list), we need to configure a profile list here as well. Edit and update the following configuration per the community requesting the hub needs.

    ```yaml
    jupyterhub:
      singleuser:
        profileList:
          - display_name: "Only Profile Available, this info is not shown in the UI"
            slug: only-choice
            profile_options:
              image:
                display_name: Image
                unlisted_choice:
                  enabled: True
                  display_name: "Custom image"
                  validation_regex: "^.+:.+$"
                  validation_message: "Must be a publicly available docker image, of form <image-name>:<tag>"
                  display_name_in_choices: "Specify an existing docker image"
                  description_in_choices: "Use a pre-existing docker image from a public docker registry (dockerhub, quay, etc)"
                  kubespawner_override:
                    image: "{value}"
                choices:
                  pangeo:
                    display_name: Pangeo Notebook Image
                    description: "Python image with scientific, dask and geospatial tools"
                    kubespawner_override:
                      image: pangeo/pangeo-notebook:2023.09.11
                  scipy:
                    display_name: Jupyter SciPy Notebook
                    slug: scipy
                    kubespawner_override:
                      image: quay.io/jupyter/scipy-notebook:2024-03-18
    ```

## Setup the image registry

### For GCP (via terraform)

If the hub will be deployed on a GCP cluster, we can setup [gcr.io](https://gcr.io) via the [terraform config](https://github.com/2i2c-org/infrastructure/blob/main/terraform/gcp/registry.tf).

1. Enable the repository creation by adding the following in the cluster's terraform config:

    ```terraform
    container_repos = [
      "some-other-repository",
      "<repository-name>",
    ]
    ```

    where <repository-name> is the name of the repository where all the images built from the hub will be pushed.

    ```{note}
    If a `container_repos` config already exists, then, just add the new repository name to this list.
    ```

2. Get the registry credentials

   The username to access this registry is [`_json_key`](https://cloud.google.com/artifact-registry/docs/docker/authentication#json-key) and the password can be discovered by running the following terraform command:

   ```bash
   terraform output registry_sa_keys
   ```

   ```{important}
   Store these somewhere safe as we will need them in a following step.
   ```

### For other cloud providers (quay.io)

If the hub will be deployed on another cloud provider than GCP, we must setup a new [quay.io](https://quay.io) organization and a robot account to push and pull from it.

1. Go to https://quay.io/organizations/new/ and create a new organization. Give it a memorable name like <cluster-name>-<hub-name>.
2. Make sure this new organization is selected, by going to https://quay.io/organization/<new-org-name>.
3. Select the 'Robot Accounts' option on the left menu.
3. Click 'Create Robot account', give it a memorable name (such as `image_builder`) and click 'Create'.
4. In the next screen, don't select any of the existing repositories, as we need this robot account to have enough permissions to push **any** new repository under the organization, so permissions to existing repositories is not needed.
5. Once done, click the name of the robot account again. This will give you its username and password.
   ```{important}
   Store these somewhere safe as we will need them in a following step.
   ```
6. Select the 'Team and Membership' option on the left menu.
7. Click on the 'Options' wheel of the `owners` team, then select 'Manage Team Members'.
8. Type in the name of the robot account that you created, select it from the list and add it to the `owners` team.
9. Add also the other engineers as members of this new organization by searching their handles in the search bar on the right.


## Setup the `binderhub-service` chart

We will use the [binderhub-service](https://github.com/2i2c-org/binderhub-service/) Helm chart to run BinderHub, the Python software, as a standalone service to build and push images with [repo2docker](https://github.com/jupyterhub/repo2docker), next to JupyterHub.

1. Setup the `binderhub-service` config

    ```yaml
    binderhub-service:
      enabled: true
      config:
        BinderHub:
          # something like <region>-docker.pkg.dev/<project-name>/<repository-name> for grc.io
          # or quay.io/org/repo/cluster-hub/ for quay.io
          image_prefix: <repository_path>
      buildPodsRegistryCredentials:
        # registry server address like https://quay.io or https://us-central1-docker.pkg.dev
        server: <server_address>
        # robot account namer or "_json_key" if using grc.io
        username: <account_name>
    ```

2. Sops-encrypt and store the password for accessing the image registry, in the `enc-<hub>.secret.values.yaml` file.

    You should have the password for accessing the image registry from a previous step.

    ```yaml
    binderhub-service:
      buildPodsRegistryCredentials:
        password: <password>
    ```

3. If pushing to quay.io registry, also setup the credentials for image pulling

    When pushing to the quay registry, the images are pushed as `private` by default (even if the plan doesn't allow it).

    A quick workaround for this, is to use the robot's account credentials to also set [`imagePullSecret`](https://z2jh.jupyter.org/en/stable/resources/reference.html#imagepullsecret) in the `enc-<hub>.secret.values.yaml`:

    ```yaml
    jupyterhub:
      imagePullSecret:
          create: true
          registry: quay.io
          username: <robot_account_name>
          password: <password>
    ```
