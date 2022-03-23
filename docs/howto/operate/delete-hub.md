# Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Remove the hub values file**.
   Without removing the values file from the repository first, the hub could be redeployed by any merged PR that triggers our CI/CD pipeline.
   Open a PR that removes the appropriate `config/clusters/<cluster_name>/<hub_name>.values.yaml` file, and removes the associated hub entry from the `config/clusters/<cluster_name>/cluster.yaml` file.
   Steps 2 and 3 can be actioned while this PR is reviewed and merged.

2. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.

3. **Backup the home directory contents**.  Especially if we think that
   users will want this information in the future (or if we plan to re-deploy a
   hub elsewhere).

4. **Delete the Helm release**. In the appropriate cluster,
   run `helm --namespace <hub-name> delete <hub-name>`

5. **Delete the kubernetes namespace**. In the appropriate cluster, run
   `kubectl delete namespace <hub-name>`, to cleanup any possible leftovers that
   step (3) missed

6. **Delete the OAuth application**.  For each hub that uses Auth0, we create an
   [Application](https://auth0.com/docs/applications) in Auth0.  There is a
   limited number of Auth0 applications available, so we should delete the one
   used by this hub when it's done.  You should be able to see the [list of
   applications](https://manage.auth0.com/dashboard/us/2i2c/applications) if you
   login to auth0 with your 2i2c google account.

   Similarly, for each hub that uses CILogon, we dynamically create an OAuth
   [client application](https://cilogon.github.io/oa4mp/server/manuals/dynamic-client-registration.html)
   in CILogon using the [cilogon_app.py](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/cilogon_app.py)
   script. Use the script to delete this CILogon client when a hub is removed.

   ```bash
   python deployer/cilogon_app.py delete <cluster-name> <hub-name>
   ```
