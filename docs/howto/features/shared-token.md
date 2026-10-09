(howto:shared-token)=
# Set a secret environment variable in user servers

Communities sometimes ask us to make a shared token (for example an API key) available to every user on their hub.
We set it as an environment variable in user servers, stored in a `sops`-encrypted values file.
Communities request this by following [the user docs](https://docs.2i2c.org/admin/security/managing-secrets/).

1. Decrypt the hub's `enc-<name>.secret.values.yaml` under `config/clusters/<cluster>/`.
   Create it if it does not exist, and list it under `helm_chart_values_files` in `cluster.yaml`.
   See [](#secrets:naming-conventions).
2. Add the variable under `jupyterhub.singleuser.extraEnv`:

   ```yaml
   jupyterhub:
     singleuser:
       extraEnv:
         MY_SERVICE_TOKEN: "<value>"
   ```

3. Re-encrypt and open a PR.
   When you merge the PR, the hub change will be deployed.
4. Ask users to restart their server and they should see the variable.

:::{note} Example from one of our communities
See: https://github.com/2i2c-org/infrastructure/pull/6909
:::
