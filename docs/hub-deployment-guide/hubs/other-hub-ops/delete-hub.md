# Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

## 1. Manage existing data

The existing data should either be migrated to another place or should be deleted, depending on what has been aggreed to with the Community Representative.

If the data should be migrated from the hub before decommissioning, then make sure that a 2i2c Engineer has access to the destination in order to complete the data migration.

The sub-sections below cover both scenarios.

### 1.1. Migrate data

#### 1.1.1 Backup the hub database

[Backup the `jupyterhub.sqlite` database](https://infrastructure.2i2c.org/en/latest/howto/hubs/move-hub.html#transfer-the-jupyterhub-database) off the hub.

#### 1.1.2. Backup the home directory contents.

Especially if we think that users will want this information in the future (or if we plan to re-deploy a hub elsewhere).

### 1.2. Delete data

Delete user home directories using the [deployer `exec-homes-shell`](https://github.com/2i2c-org/infrastructure/blob/master/deployer/README.md#exec-homes-shell) option.

```bash
python3 deployer.debug exec-homes-shell <cluster_name> <hub_name>
```

This should get you a shell with the home directories of all the users on the given hub. Delete all user home directories with:

```bash
cd home
rm -rf *
```

## 2. Remove the hub values file

Without removing the values file from the repository first, the hub could be redeployed by any merged PR that triggers our CI/CD pipeline.

Open a PR that removes the appropriate `config/clusters/<cluster_name>/<hub_name>.values.yaml` file, and removes the associated hub entry from the `config/clusters/<cluster_name>/cluster.yaml` file. A complete list of relevant files can be found under the appropriate entry in the associated `cluster.yaml` file.

Steps 3 and 4 can be actioned while this PR is reviewed and merged.

## 3. Delete the Helm release

In the appropriate cluster, run:

```bash
helm --namespace <hub-name> delete <hub-name>
```

## 4. Delete the kubernetes namespace

In the appropriate cluster, run:

```bash
kubectl delete namespace <hub-name>
```

to cleanup any possible leftovers that step (4) missed

## 5. Delete the OAuth application

### Auth0 OAuth application

For each hub that uses Auth0, we create an [Application](https://auth0.com/docs/applications) in Auth0.  There is a limited number of Auth0 applications available, so we should delete the one used by this hub when it's done. You should be able to see the [list of applications](https://manage.auth0.com/dashboard/us/2i2c/applications) if you login to auth0 with your 2i2c google account.

### GitHub OAuth application

For each hub that uses the JupyterHub GitHubOAuthenticator, we create a GitHub [OAuth Application](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app). You should be able to see the list of applications created under the `2i2c` GitHub org and delete the one created for the hub that's being decommissioned.

The naming convention followed when creating these apps is: `<cluster_name>-<hub_name>.

### CILogon OAuth application

Similarly, for each hub that uses CILogon, we dynamically create an OAuth [client application](https://cilogon.github.io/oa4mp/server/manuals/dynamic-client-registration.html) in CILogon using the [cilogon_app.py](https://github.com/2i2c-org/infrastructure/blob/HEAD/deployer/cilogon_app.py)
script. Use the script to delete this CILogon client when a hub is removed:

You'll need to get all clients with:

```bash
python3 deployer/cilogon_app.py get-all
```

And then identitify the client of the hub and delete based on its id with:

```bash
python3 deployer/cilogon_app.py delete --id cilogon:/client_id/<id>
```
