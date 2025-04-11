# Shared Password Authentication

This documentation covers setting up a hub to have a shared password for login using the [Dummy Authenticator](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#the-dummy-authenticator)
for a hub.

For this section, it may be useful to set the following environment variables in your terminal.

```bash
export CLUSTER_NAME=cluster_name
export HUB_NAME=hub_name
```

## Use a specific branch of the homepage repository

The Dummy Authenticator requires presenting the user with a username and password input field, rather than the typical "log in" button.
This means we cannot use the default homepage template since this will not provide these input fields.
Instead we use a specialised branch of the homepage repo which allows us to have the username and password input fields, along with providing specific info about and for each community: [`bootstrap5-username-and-password-homepage`](https://github.com/2i2c-org/default-hub-homepage/tree/bootstrap5-username-and-password-homepage).

In the `${HUB_NAME}.values.yaml` file, include the following config.

```yaml
jupyterhub:
  custom:
    homepage:
      gitRepoBranch: "bootstrap5-username-and-password-homepage"
      templateVars: [...]  # These values are as normal
```

## Using a global password

We **only** support using a global password with this method of authentication.
A global password is simple to distribute to a large group of people for a specific event, such as a workshop, while still locking the hub down from the public which can protect it from cryptomining abuse.

Enable the Dummy Authenticator in the `${HUB_NAME}.values.yaml` file with the following config.

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: dummy
```

Then, in a `${HUB_NAME}.secret.values.yaml` file, include the password.

```yaml
jupyterhub:
  hub:
    config:
      DummyAuthenticator:
        password: <password>
```

You can then encrypt the password using the below `sops` command.

```bash
sops --output config/clusters/${CLUSTER_NAME}/enc-${HUB_NAME}.secret.values.yaml -e config/clusters/${CLUSTER_NAME}/${HUB_NAME}.secret.values.yaml
```

Ensure both these files are listed in the related `cluster.yaml` file.

```yaml
[...]
hubs:
  - name: ...
    display_name: ...
    domain: ...
    helm_chart: ...
    helm_chart_values_files:
      - ${HUB_NAME}.values.yaml
      - enc-${HUB_NAME}.secret.values.yaml
```

### How the community should request changing the password

If the community wishes to change the global password, they should do so by [submitting a ticket the support team](https://docs.2i2c.org/support/).

## Disabling admin users

Since using the Dummy Authenticator will allow any username with the correct password to login, this opens scope for a user to login with an admin username and gain admin rights.
Hence, we disable all admins on the hub to prevent this.
We do this by not providing anything to `jupyterhub.hub.config.Authenticator.admin_users`.

However if the hub is sharing config with another, e.g. via a `common.values.yaml` file, you may need to explicitly disable admin users with the following config in the `${HUB_NAME}.values.yaml` file.

```yaml
jupyterhub:
  hub:
    config:
      Authenticator:
        admin_users: []
```

## Disabling shared/shared-read-write directories

Since there are no admin users on shared passwords hub, there's no point in having a shared directory.
We can disable this by setting the following in the `${HUB_NAME}.values.yaml` file.

```yaml
jupyterhub:
  custom:
    singleuserAdmin:
      extraVolumeMounts: []
  singleuser:
    initContainers:
      - name: volume-mount-ownership-fix
        image: busybox:1.36.1
        command:
          - sh
          - -c
          - id && chown 1000:1000 /home/jovyan && ls -lhd /home/jovyan
        securityContext:
          runAsUser: 0
        volumeMounts:
          - name: home
            mountPath: /home/jovyan
            subPath: "{escaped_username}"
    storage:
      extraVolumeMounts: []
```

## Disabling the configurator

For the same reason as above, we also need to disable the configurator as this is an admin-only feature.

```yaml
jupyterhub:
  custom:
    jupyterhubConfigurator:
      enabled: false
```
