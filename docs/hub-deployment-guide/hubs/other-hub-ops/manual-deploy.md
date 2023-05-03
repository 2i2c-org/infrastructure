(hubs:manual-deploy)=
# Manually deploy a config change

While deploys generally go through our GitHub Actions workflow, sometimes you
need to deploy from your laptop - primarily when testing changes on staging or
actively fixing an outage. After doing a manual deploy, you *must* make a PR and
get it deployed as soon as possible - otherwise your changes might get reverted
the next time a different PR is merged and deploys to the hub you deployed to!

Our deployment scripts live in the [`deployer/`](https://github.com/2i2c-org/infrastructure/tree/HEAD/deployer/)
of this repository, and can deploy one or more hubs to our clusters.

## Deploy a single hub

1. [Setup your local environment](tutorials:setup) to be able to do deploys

2. Make the [config change](../../../topic/infrastructure/config.md) you want to deploy.

3. Deploy just a single hub:

   ```bash
   export CLUSTER_NAME=<cluster-name>
   export HUB_NAME=<hub-name>
   ```

   ```bash
   deployer deploy $CLUSTER_NAME $HUB_NAME
   ```

   The script will look for a hub named `$HUB_NAME` in the cluster config
   defined at `config/clusters/$CLUSTER_NAME/cluster.yaml` and read in the `*.values.yaml` files associated with that hub.

4. You can deploy to *all* hubs on a given cluster by omitting the hub name.

   ```bash
   deployer deploy $CLUSTER_NAME
   ```

```{note}
You should mostly use the `staging` hub in the `2i2c` cluster for testing.
```

(hubs:manual-deploy:health-check)=
## Run a health check on the hub

After doing a deploy, you should run a health check on the hub you just
deployed to make sure it continues to function. You can do this manually, but
there's also some automation that runs through some basic tests.

The automated test, creates a new hub user called `deployment-service-check`, starts a
server for them, and runs the test notebooks.  It checks that the notebook
runs to completion and the output cells have the expected value.

* If the health check passes, then the user's server is stopped and deleted.
* If the health check fails, then their user server will be left running, but
* it will get deleted together with the user in the next iteration.

To run the automated health check on a hub, run

```bash
deployer run-hub-health-check $CLUSTER_NAME $HUB_NAME
```

This will test a simple notebook, but not any dask functionality. To test dask
functionality as well, run

```bash
deployer run-hub-health-check --check-dask-scaling $CLUSTER_NAME $HUB_NAME
```

These tests are automatically run when you deploy via CI.
