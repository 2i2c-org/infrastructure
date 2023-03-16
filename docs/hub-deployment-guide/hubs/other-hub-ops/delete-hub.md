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
export CLUSTER_NAME=<cluster-name>
export HUB_NAME=<hub-name>
```

```bash
deployer exec-homes-shell $CLUSTER_NAME $HUB_NAME
```

This should get you a shell with the home directories of all the users on the given hub. Delete all user home directories with:

```bash
# list the folders before running the command to delete them all
ls -lh /home

# this can take tens of minutes
rm -rf /home/*
```

## 2. Remove the hub values file

If the hub remains listed in its cluster's `cluster.yaml` file, the hub could be
redeployed by any merged PR triggering our CI/CD pipeline.

Open a decomissioning PR that removes the appropriate hub entry from the
`config/clusters/$CLUSTER_NAME/cluster.yaml` file and associated
`*.values.yaml` files no longer referenced in the `cluster.yaml` file.

You can continue with the steps below before the PR is merged, but be ready to
re-do them if the CI/CD pipeline was triggered before the decomissioning PR was
merged.

## 3. Delete the Helm release and namespace

In the appropriate cluster, run:

```bash
deployer use-cluster-credentials $CLUSTER_NAME

helm --namespace=$HUB_NAME delete $HUB_NAME
kubectl delete namespace $HUB_NAME
```

## 4. Delete the OAuth application

### Auth0 OAuth application

For each hub that uses Auth0, we create an [Application](https://auth0.com/docs/applications) in Auth0.  There is a limited number of Auth0 applications available, so we should delete the one used by this hub when it's done. You should be able to see the [list of applications](https://manage.auth0.com/dashboard/us/2i2c/applications) if you login to auth0 with your 2i2c google account.

### GitHub OAuth application

For each hub that uses the JupyterHub GitHubOAuthenticator, we create a GitHub [OAuth Application](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app). You should be able to see the [list of applications created under the `2i2c` GitHub org](https://github.com/organizations/2i2c-org/settings/applications) and delete the one created for the hub that's being decommissioned.

The naming convention followed when creating these apps is: `$CLUSTER_NAME-$HUB_NAME`.

### CILogon OAuth application

Similarly, for each hub that uses CILogon, we dynamically create an OAuth [client application](https://cilogon.github.io/oa4mp/server/manuals/dynamic-client-registration.html) in CILogon using the `deployer cilogon-client-create` command.
Use the `deployer cilogon-client-delete` command to delete this CILogon client when a hub is removed:

You'll need to get all clients with:

```bash
deployer cilogon-client-get-all
```

And then identify the client of the hub and delete based on its id with:

```bash
deployer cilogon-client-delete --client_id cilogon:/client_id/<id>
```
