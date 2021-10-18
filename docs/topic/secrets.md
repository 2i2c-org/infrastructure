# Secrets and private keys

(secrets:locations)=
## Where are secrets stored

Most secrets are stored in one of two locations:

https://github.com/2i2c-org/pilot-hubs/blob/master/config/secrets.yaml
: Credentials for all of the clusters that we run (across all cloud providers).


https://github.com/2i2c-org/pilot-hubs/blob/master/config/secrets.yaml
: `Auth0` and proxy secrets for all of our hubs.

Both are encrypted with [`sops`](https://github.com/mozilla/sops).

:::{seealso}
For information about how to set up `sops`, see [the team compass documentation](tc:secrets:sops)
:::

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
   If you wish to change the secret keys for the hub proxies, you would update the value of `secret_key` in [the configuration file with proxy secrets](https://github.com/2i2c-org/pilot-hubs/blob/master/config/secrets.yaml).
   :::

5. Re-encrypt the file with `sops`.
6. Commit the file to the repository and push.

You have now rotated the secret for this key!
