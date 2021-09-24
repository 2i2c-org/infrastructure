# Secrets and private keys

## Where are secrets stored

Most secrets are stored in this location:

https://github.com/2i2c-org/pilot-hubs/blob/master/config/secrets.yaml

This contains a configuration file encrypted with [`sops`](https://github.com/mozilla/sops).
It is used for things like authentication with `Auth0`, image registries, etc.

:::{seealso}
For information about how to set up `sops`, see [the team compass documentation](tc:secrets:sops)
:::

## How to rotate / change secrets

Sometimes we need to rotate the secret keys used in our repository.
For example, if a service we use has become compromised, and we need to generate new keys in order to protect the infrastructure.

To rotate our secrets, take these steps:

1. Unencrypt [our configuration file](https://github.com/2i2c-org/pilot-hubs/blob/master/config/secrets.yaml) (see [the team compass documentation](tc:secrets:sops) for instructions).
2. Generate a new key with `openssl`:
   
   ```
   openssl rand -hex 32
   ```
   
   This will return a random hash that looks something like this:

   ```
   4a87d32d435f5471b5852f30f1adcc29d11b39035d68b81720130701e65fa585
   ```

3. Find the key you'd like to replace, and replace its value with the hash that you've generated above.
4. Re-encrypt the file with `sops`.
5. Commit the file to the repository and push.

You have now rotated the secret for this key!
