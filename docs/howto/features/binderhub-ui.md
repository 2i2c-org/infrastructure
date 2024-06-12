# Make binderhub-ui hub

We can support users who want to build, push and launch user images, from open source GitHub repositories, from an UI similar with [mybinder.org](https://mybinder.org).

We call this a `binderhub-ui` style hub and the primary features offered would be:

- **User authentication**
- **NO Persistent storage**
- **BinderHub style UI**

## Important architectural decisions made

1. **Two separate domains, one for binderhub UI and one for the jupyterhub**
1. **A logged out homepage, and a logged-in homepage**


## Setup jupyterhub.custom config

Under `jupyterhub.custom` there are a few configuration options that need to be set in the following way:

1. disable the `jupyterhub-configurator`
1. enable the `binderhubUI`, which will in turn allow us to convert JupyterHub container spawners into BinderHub spawners
1. use a simpler landing page, i.e. the page where users land to login into the hub before actually seeing the binderhub UI. This is done by having the hub track the `no-homepage-subsections` branch of the default homepage repo
1. disable `singleuserAdmin.extraVolumeMounts` (no persistent storage so these don't make sense)

```yaml
jupyterhub:
  custom:
    jupyterhubConfigurator:
      enabled: false
    binderhubUI:
      enabled: true
    homepage:
      gitRepoBranch: "no-homepage-subsections"
      templateVars:
        (...)
    singleuserAdmin:
      extraVolumeMounts: []
```

## Disable user storage

There will be no persistent storage, so disable it. Because of this `singleuser.extraVolumeMounts` and `singleuser.initContainers` should also be emptied.

```yaml
jupyterhub:
  singleuser:
    storage:
      type: none
      extraVolumeMounts: []
    initContainers: []
```

## Configure the hub services, roles and spawner

There are a few configurations that need to be made on the hub side:

1. setup `binder` as a jupyterhub externally managed service
1. setup a `binder` and a `user` role and make sure the correct permissions are being assigned to this new service but also to the users so that they can access the service.
1. enable authenticated binderhub spawner setup via `hub.config.BinderSpawnerMixin.auth_enabled`

```yaml
jupyterhub:
  hub:
    redirectToServer: false
    services:
      binder:
        # skip the OAuth confirmation page
        oauth_no_confirm: true
        # the service will have a public url instead of being contacted via /services/:name
        oauth_redirect_uri: https://<binderhub-public-url>/oauth_callback
    loadRoles:
      # The role binder allows service binder to start and stop servers
      # and read (but not modify) any user’s model
      binder:
        services:
          - binder
        scopes:
          - servers
          - read:users # admin:users is required if authentication isn't enabled
      # The role user allows access to the user’s own resources and to access
      # only the binder service
      user:
        scopes:
          - self
          # Admin users will by default have access:services, so this is only
          # observed to be required for non-admin users.
          - access:services!service=binder
    config:
      BinderSpawnerMixin:
        auth_enabled: true
```

## Setup the image registry

Follow the guide at [](howto:features:imagebuilding-hub:image-registry) of the imagebuilding hub.

## Setup the `binderhub-service` chart

We will use the [binderhub-service](https://github.com/2i2c-org/binderhub-service/) Helm chart to run BinderHub, the Python software, as a standalone service to build and push images with [repo2docker](https://github.com/jupyterhub/repo2docker), next to JupyterHub.

1. Setup the `binderhub-service` config

    ```yaml
    binderhub-service:
      enabled: true
      # enable the binderhub-service ingress and configure it
      # so that we get a public domain for binderhub to run
      ingress:
        enabled: true
        hosts:
          - <binderhub-public-url>.2i2c.cloud
        tls:
          - secretName: binder-https-auto-tls
            hosts:
              - <binderhub-public-url>.2i2c.cloud
      config:
        BinderHub:
          base_url: /
          hub_url: https://<jupyterhub-public-url>.2i2c.cloud
          badge_base_url: https://<binderhub-public-url>.2i2c.cloud
          auth_enabled: true
          enable_api_only_mode: false
          image_prefix: <repository_path>
      buildPodsRegistryCredentials:
        # registry server address like https://quay.io or https://us-central1-docker.pkg.dev
        server: <server_address>
        # robot account namer or "_json_key" if using grc.io
        username: <account_name>
      extraConfig:
        # FIXME: set KubernetesBuildExecutor.push_secret again
        #        without this for some reason the build pods
        #        search after the wrong secret name (i.e. the default name)
        #        set by binderhub in KubernetesBuildExecutor.push_secret
        01-binderhub-service-set-push-secret: |
          import os
          c.KubernetesBuildExecutor.push_secret = os.environ["PUSH_SECRET_NAME"]
      extraEnv:
        - name: JUPYTERHUB_API_TOKEN
          valueFrom:
            # Any JupyterHub Services api_tokens are exposed in this k8s Secret
            secretKeyRef:
              name: hub
              key: hub.services.binder.apiToken
        - name: JUPYTERHUB_CLIENT_ID
          value: "service-binder"
        - name: JUPYTERHUB_API_URL
          value: "https://<hub-public-url>.2i2c.cloud/hub/api"
        # Without this, the redirect URL to /hub/api/... gets
        # appended to binderhub's URL instead of the hub's
        - name: JUPYTERHUB_BASE_URL
          value: "https://<hub-public-url>.2i2c.cloud/"
        - name: JUPYTERHUB_OAUTH_CALLBACK_URL
          value: "https://<binderhub-public-url>.2i2c.cloud/oauth_callback"
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
