(secrets:top)=
# Secrets and private keys

(secrets:locations)=
## Where are secrets stored

Most secrets are stored in one of two locations:

https://github.com/2i2c-org/infrastructure/tree/HEAD/shared/deployer/
: Secrets that are shared across all of our hub and cluster deployments, such as Auth0 secrets.

Secrets that are specific to each cluster / hub that we run - for example, cloud provider secrets to control the cluster programmatically - are stored in that cluster's directory under `config/clusters`.
For example, see the [2i2c cluster directory](https://github.com/2i2c-org/infrastructure/tree/HEAD/config/clusters/2i2c).

All our secrets are encrypted with [`sops`](https://github.com/mozilla/sops).

:::{seealso}
For information about how to set up `sops`, see [the team compass documentation](https://compass.2i2c.org/engineering/secrets/)
:::

(secrets:naming-conventions)=
## Naming conventions for secret files

All our secrets should contain the word `secret` somewhere in their filename since this will ensure they will be git-ignored in their unencrypted format.
For unencrypted secret files, we follow the convention:

```bash
descriptive-name.secret.yaml
```

When we encrypt this file using `sops`, our convention is to add the prefix `enc-`.
This will tell `git` that the file is encrypted and therefore safe to be checked into version control.
You can change the name of the file during encryption like so:

```bash
sops --output enc-descriptive-name.secret.yaml --encrypt descriptive-name.secret.yaml
```

Similarly, we remove the `enc-` prefix when decrypting a file so it can no longer be checked into version control, like so:

```bash
sops --output descriptive-name.secret.yaml --decrypt enc-descriptive-name.secret.yaml
```

## How to rotate / change secrets

Sometimes we need to rotate the secret keys used in our repository.
For example, if a service we use has become compromised, and we need to generate new keys in order to protect the infrastructure.

To rotate our secrets, take these steps:

1. Determine which configuration file you'd like to update. See [](secrets:locations).
2. Unencrypt the configuration file. See [the team compass documentation](tc:secrets:sops) for instructions on unencrypting.
3. Generate a new key with `openssl`:

   ```
   openssl rand -hex 32
   ```

   This will return a random hash that looks something like this:

   ```
   4a87d32d435f5471b5852f30f1adcc29d11b39035d68b81720130701e65fa585
   ```

4. Find the key you'd like to replace, and replace its value with the hash that you've generated above.

   :::{admonition} Example
   If you wish to change the secret keys for the hub proxies, you would update the value of `secret_key` in [the configuration file with proxy secrets](https://github.com/2i2c-org/infrastructure/blob/HEAD/shared/deployer/enc-auth-providers-credentials.secret.yaml).
   :::

5. Re-encrypt the file with `sops`.
6. Commit the file to the repository and push.

You have now rotated the secret for this key!

(secrets:cleaning)=
## Cleaning up decrypted files

The [naming conventions](secrets:naming-conventions) we outlined above allow us to clean the repository of unencrypted secrets using our [`.gitignore` config](https://github.com/2i2c-org/infrastructure/blob/HEAD/.gitignore#L6-L16) and the `git clean` command.

To clean up unencrypted secrets (and other ignored files) you can use `git clean -Xfd` which will delete untracked files (`-X`), with required confirmation (`-f`), recursively (`-d`).
