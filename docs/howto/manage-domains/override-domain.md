# Override a hub's domain name

This guide aims provides an overview of how to override the domain name of a hub and why you may want to do this.

## Motivation

In the past, the engineering team have been asked to provide a temporary, alternative domain name for a hub to make it undiscoverable.
This could be for reasons such as:

- prevent a class from accessing an educational hub while investigations around cheating are ongoing
- make the hub undiscoverable by crypto-miners

```{danger}
This is generally a temporary fix to rapidly make a hub undiscoverable and should not replace or take priority over processes that more robustly address the above concerns.
```

## How-to guide

1. Create a new file with the path `config/clusters/$CLUSTER_NAME/<hub_name>.domain_override.secret.yaml` where `<hub_name>` is the name of the hub we are targeting, and `$CLUSTER_NAME` is the name of the cluster upon which the hub is running.
   ```{note}
   We have included `secret` in the filename since we will be encrypting this file with `sops` so that the new domain name cannot be discovered by someone checking the GitHub repository.
   However, it is worth noting that our deployment infrastructure does not _enforce_ the domain override file to be encrypted and an unencrypted file can be provided, if necessary.
   ```
2. Add the new domain to the new domain override file like so:

   ```yaml
   domain: ENTER_NEW_DOMAIN_HERE
   ```

   ```{note}
   The new domain still still follow the convention `foo.$CLUSTER_NAME.2i2c.cloud`, but `foo` can be replaced with anything that is not the current top-level domain of the hub.
   A randomly generated string is probably best to avoid the new domain being guessable.
   ```
3. (Optional) Encrypt the file with `sops`.

   ```bash
   export CLUSTER_NAME=<cluster-name>
   export HUB_NAME=<hub-name>
   ```

   ```bash
   sops --output config/clusters/$CLUSTER_NAME/enc-$HUB_NAME.domain_override.secret.yaml --encrypt config/clusters/$CLUSTER_NAME/$HUB_NAME.domain_override.secret.yaml
   ```

   The file can now be safely committed to the repository.
4. Update the `cluster.yaml` file to list the domain override file.

   ```yaml
   hubs:
     ...
     - name: <hub-name>
       domain: original.domain.2i2c.cloud
       domain_override_file: enc-<hub-name>.domain-override.secret.yaml
   ```

   ```{note}
   This filepath is defined _relative_ to the location of the `cluster.yaml` file.
   ```

5. Run the deployer for the hub!

   ```bash
   deployer deploy $CLUSTER_NAME $HUB_NAME
   ```
