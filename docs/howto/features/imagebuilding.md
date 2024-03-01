# Make an imagebuilding hub

We can support users who want to build, push and launch user images, from open source GitHub repositories, similar with what [mybinder.org](https://mybinder.org) does, but from within their JupyterHubs

We call this an `imagebuilding` style hub and the primary features offered would be:

1. User authentication
2. Persistent storage
3. Server options allowing:
  - pre-defined list of images to choose from
  - specifying another image, different from the ones in the pre-defined list
  - building and pushing an image to a registry from a GitHub repository

## Use the `dynamic-image-building-experiment` hub image

We will need to use `jupyterhub-fancy-profiles`, but this Python package isn't installed in the default image deployed with our hubs, so we should use the [`dynamic-image-building-experiment` hub image](https://github.com/2i2c-org/infrastructure/blob/master/helm-charts/images/hub/dynamic-image-building-requirements.txt) instead.

```yaml
jupyterhub:
  hub:
    image:
      name: quay.io/2i2c/dynamic-image-building-experiment
      tag: "0.0.1-0.dev.git.7567.ha4162031"
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
                    image: jupyter/scipy-notebook:2023-06-26
    ```

## The `binderhub-service` chart

We will use the [binderhub-service](https://github.com/2i2c-org/binderhub-service/) Helm chart to run BinderHub, the Python software, as a standalone service to build and push images with [repo2docker](https://github.com/jupyterhub/repo2docker), next to JupyterHub.

### How it works

The `binderhub-service` installation starts a `docker-api` pod on each of the user nodes via the following [DaemonSet definition](https://github.com/2i2c-org/binderhub-service/blob/main/binderhub-service/templates/docker-api/daemonset.yaml).

The `docker-api` pod setups and starts the [dockerd](https://docs.docker.com/engine/reference/commandline/dockerd/) daemon, that will then be accessible via a mounted unix socket on the node, by the `build pods`.

The `build pods` are created as a result of an image build request, and they must run on the same node as the builder pods to make use of the docker daemon. These pods mount a k8s Secret with the docker config file holding the necessary registry credentials so they can push to the container registry.

### How to set it up

1. Setup a registry and safely store the credentials to push to it

  - If the hub will be deployed on a GCP cluster, follow the steps 4 to 8 from the [binderhub-service installation guide](https://github.com/2i2c-org/binderhub-service?tab=readme-ov-file#installation). When you're done, you should have a gcr.io registry setup and the appropriate credentials to push images to it.

  - If the hub will be deployed on another cloud provider than GCP, then you should setup the desired quay.io repository and robot account to push and pull from it. The steps below describes how to create one under the 2i2c quay.io organization, assuming this is where we wish the repositories that will be build by `binderhub-service` to be pushed.

    - Go to https://quay.io/organization/2i2c
    - Select the 'Robot Accounts' option on the left menu.
    - Click 'Create Robot account', give it a memorable name (such as `<cluster_name>_<hub-name>_image_builder`) and click 'Create'
    - In the next screen, don't select any of the existing repositories, as we need this robot account to have enough permissions to push **any** new repository under the organization and permissions to existing repositories is not needed.
    - Once done, click the name of the robot account again. This will give you its username and password.
    - Select the 'Team and Membership' option on the left menu.
    - Click on the 'Options' wheel of the `owners` team, then select 'Manage Team Members'
    - Type in the name of the robot account that you created, select it from the list and add it to the `owners` team


2. Setup the `binderhub-service` config

  ```yaml
  binderhub-service:
    nodeSelector:
      hub.jupyter.org/node-purpose: core
    enabled: true
    # Set a port on which the binderhub-service ClusterIP Service will run
    service:
      port: 8090
    dockerApi:
      nodeSelector:
        # The dockerApi pods need to run on the same user nodes as the user pods
        hub.jupyter.org/node-purpose: user
      tolerations:
        # Tolerate tainted jupyterhub user nodes
        - key: hub.jupyter.org_dedicated
          value: user
          effect: NoSchedule
        - key: hub.jupyter.org/dedicated
          value: user
          effect: NoSchedule
    config:
      BinderHub:
        # jupyterhub-fancy-profile expects binderhub to be available under http://{{hub url}}/services/binder
        base_url: /services/binder
        use_registry: true
        # something like <region>-docker.pkg.dev/<project-name>/<repository-name> for grc.io
        # or quay.io/org/repo/cluster-hub/ for quay.io
        image_prefix: <repository_path>
      KubernetesBuildExecutor:
        # Get ourselves a newer repo2docker!
        build_image: quay.io/jupyterhub/repo2docker:2023.06.0-8.gd414e99
        node_selector:
          # Schedule builder pods to run on user nodes only
          hub.jupyter.org/node-purpose: user
    # The password to the registry is stored encrypted in the hub's encrypted config file
    buildPodsRegistryCredentials:
      # registry server address like https://quay.io
      server: <server_address>
      # robot account namer or "_json_key" if using grc.io
      username: <account_name>
  ```

3. Sops-encrypt and store the password of the registry account, in the `enc-<hub>.secret.values.yaml` file.

  ```yaml
  buildPodsRegistryCredentials:
    password: |
      <json_key_from_service_account>
  ```

4. If pushing to quay.io registry, also setup the credentials for image pulling

  When pushing to the quay registry, the images are pushed as `private` by default (even if the plan doesn't allow it).

  A quick workaround for this, is to use the robot's account credentials to also set [`imagePullSecret`](https://z2jh.jupyter.org/en/stable/resources/reference.html#imagepullsecret) in the `enc-<hub>.secret.values.yaml`:

  ```yaml
  jupyterhub:
    imagePullSecret:
        create: true
        registry: quay.io
        username: <robot_account_name>
        password: <account_password>
  ```
