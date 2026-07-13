# Shared Password Authentication

This documentation covers setting up a hub to have a shared password for login using the
[Shared Password Authenticator](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#shared-password-authenticator)

```{note}
We used to use the
[Dummy Authenticator](https://jupyterhub.readthedocs.io/en/stable/reference/authenticators.html#the-dummy-authenticator)
instead. That is deprecated
```

For this section, it may be useful to set the following environment variables in your terminal.

```bash
export CLUSTER_NAME=cluster_name
export HUB_NAME=hub_name
```

## Use a specific branch of the homepage repository

Until [this PR](https://github.com/2i2c-org/default-hub-homepage/pull/51)
is merged, we need to explicitly specify that as the
branch to use so login pages show the username / password
correctly.

In the `${HUB_NAME}.values.yaml` file, include the following config.

```yaml
jupyterhub:
  custom:
    homepage:
      # Remove once https://github.com/2i2c-org/default-hub-homepage/pull/51
      # is merged
      gitRepoBranch: unify-logins-2
```

## Set a *regular* user password and an *admin* password

When using the shared password method, you can have *two* passwords:

1. A *regular* user password, to be distributed to all users. Anyone can login with this
   password and an arbitrary username. This *must* be at least **8 characters** in length.

2. (Optional) An *admin* user password, to be distributed *just* to admins. Anyone whose name is
   listed as an admin user (through `Authenticator.admin_users` config) can log in when
   using this admin password. This must be at least **32 characters** in length, as admin
   users have additional powers (such as shared directory access, being able to list of
   users logged in, access anyone's home directory, etc).

Enable the Shared Password Authenticator in the `${HUB_NAME}.values.yaml` file with the following config.

```yaml
jupyterhub:
  hub:
    config:
      JupyterHub:
        authenticator_class: shared-password
        Authenticator:
          # We don't use the per-group password feature of shared-passwords yet
          manage_groups: false
          # Allow everyone with the password to log in
          allow_all: true
          # List of admin users, *if* admin_password is set in the next step
          admin_users:
          - <admin1>
          - <admin2>
```

Then, in the `sops` encrypted `enc-${HUB_NAME}.secret.values.yaml` file, include the passwords.

```yaml
jupyterhub:
  hub:
    config:
      SharedPasswordAuthenticator:
        user_password: <password>
```


### How the community should request changing the password

If the community wishes to change the global password or the admin, they should
do so by [submitting a ticket the support team](https://docs.2i2c.org/support/).
