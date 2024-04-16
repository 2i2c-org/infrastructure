# Move a Hub to a new URL

Sometimes we may want to change the URL and naming convention of a hub
we have deployed, e.g., renaming the previous 'researchdelight' hub to 'showcase' <https://github.com/2i2c-org/infrastructure/issues/3279>.

1. Rename config files and update file references

    Our [naming conventions](config) mean that we have config files in the
    form `<hub-name>.values.yaml` and these are explicitly listed as a hub
    entry within the associated `cluster.yaml` file where the hub is
    deployed. These files should be renamed `<old-hub-name>.values.yaml`
    --> `<new-hub-name>.values.yaml` and updated in the associated
    `cluster.yaml` file.

1. Update instance of the old hub name _within_ the config files

    This will mostly be related to URLs, e.g., `jupyterhub.ingress.hosts` and OAuth callback URLs for authentication.

    ```{attention}
    Some variables, e.g. references to scratch buckets or kubernetes
    annotations, may remain the same, unless you also update the related
    terraform config. This is optional, and only recommended if consistency
    of the scratch bucket names is crucial for the community.
    ```

1. Update any instances of the old hub name in the `cluster.yaml` file

    ```{warning}
    If the `name` field is changed (as opposed to only the `display_name`
    field), this will cause the deployer/helm to deploy a new hub under a
    new namespace bearing the new hubname. The namespace bearing the old
    hub name will continue to exist and will need cleaning up manually,
    since helm does not have the concept of renaming a namespace.
    Depending on how different the new name is from the old, this is a
    judgment call to make.
    ```

1. Add a redirect from the old URL to the new one

   In the `support.values.yaml` file for the cluster, set up automatic
   redirection of users going to the old domain name to arrive at the new new
   domain name.

   ```yaml
   redirects:
     rules:
       - from: <old-domain>
         to: <new-domain>
   ```

2. Open a Pull Request with the changes for review

3. Once the PR has been approved:

    1. Update A/CNAME records in Namecheap for the new URL
    2. Update the relevant OAuth app for the new URL
    3. Merge the PR

4. If you also changed the `name` field within the
   `cluster.yaml` file, [delete the old hub namespace in helm](delete-a-hub). It is recommended to
   [migrate the data](copy-home-dirs) first.
