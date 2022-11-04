# The `deployer` module

## Summary

The `deployer` is a Python module that automates various tasks that 2i2c undertake to manage 2i2c-hosted JupyterHubs.

## Installing dependencies

You can install the `deployer`'s dependencies with `pip`.
You may wish to create a virtual environment using `venv` or `conda` first.

```bash
pip install -r requirements.txt
```

## Functions

This section describes the functions the `deployer` can carry out, their purpose, and their command line usage.

**Note:** The `deployer` must currently be invoked from the root of this repository, i.e.:

```bash
$ pwd
[...]/infrastructure/deployer
$ cd .. && pwd
[...]/infrastructure
$ python deployer [sub-command]
```

**Command line usage:**

```bash
usage: deployer [-h] {deploy,validate,deploy-support,deploy-grafana-dashboards,use-cluster-credentials,generate-helm-upgrade-jobs,run-hub-health-check,generate-cluster} ...

A command line tool to perform various functions related to deploying and maintaining a JupyterHub running on kubernetes infrastructure

positional arguments:
  {deploy,validate,deploy-support,deploy-grafana-dashboards,use-cluster-credentials,generate-helm-upgrade-jobs,run-hub-health-check,generate-cluster}
                        Available subcommands
    deploy              Install/upgrade the helm charts of JupyterHubs on a cluster
    validate            Validate the cluster.yaml configuration itself, as well as the provided non-encrypted helm chart values files for each hub or the specified hub.
    deploy-support      Install/upgrade the support helm release on a given cluster
    deploy-grafana-dashboards
                        Deploy grafana dashboards to a cluster for monitoring JupyterHubs. deploy-support must be run first!
    use-cluster-credentials
                        Modify the current kubeconfig with the deployer's access credentials for the named cluster
    generate-helm-upgrade-jobs
                        Generate a set of matrix jobs to perform a helm upgrade in parallel across clusters and hubs. Emit JSON to stdout that can be read by the strategy.matrix field of a GitHub Actions
                        workflow.
    run-hub-health-check
                        Run a health check against a given hub deployed on a given cluster
    generate-cluster    Generate files for a new cluster

options:
  -h, --help            show this help message and exit
```

### `deploy`

This function is used to deploy changes to a hub (or list of hubs), or install it if it does not yet exist.
It takes a name of a cluster and a name of a hub (or list of names) as arguments, gathers together the config files under `/config/clusters` that describe the individual hub(s), and runs `helm upgrade` with these files passed as `--values` arguments.

**Command line usage:**

```bash
usage: python deployer deploy [-h] [--config-path CONFIG_PATH] [--dask-gateway-version DASK_GATEWAY_VERSION] cluster_name [hub_name]

positional arguments:
  cluster_name          The name of the cluster to perform actions on
  hub_name              The hub, or list of hubs, to install/upgrade the helm chart for

optional arguments:
  -h, --help            show this help message and exit
  --config-path CONFIG_PATH
                        File to read secret deployment configuration from
  --dask-gateway-version DASK_GATEWAY_VERSION
                        For daskhubs, the version of dask-gateway to install for the CRDs. Default: 2022.10.0
```

### `validate`

This function is used to validate the values files for each of our hubs against their helm chart's values schema.
This allows us to validate that all required values are present and have the correct type before we attempt a deployment.

**Command line usage:**

```bash
usage: python deployer validate [-h] cluster_name [hub_name]

positional arguments:
  cluster_name  The name of the cluster to perform actions on
  hub_name      The hub, or list of hubs, to validate provided non-encrypted helm chart values for.

optional arguments:
  -h, --help    show this help message and exit
```

### `deploy-support`

This function deploys changes to the support helm chart on a cluster, or installs it if it's not already present.
This command only needs to be run once per cluster, not once per hub.

**Command line usage:**

```bash
usage: python deployer deploy-support [-h] [--cert-manager-version CERT_MANAGER_VERSION] cluster_name

positional arguments:
  cluster_name          The name of the cluster to perform actions on

optional arguments:
  -h, --help            show this help message and exit
  --cert-manager-version CERT_MANAGER_VERSION
                        The version of cert-manager to deploy in the form vX.Y.Z. Defaults to v1.3.1
```

### `deploy-grafana-dashboards`

This function uses [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) to create a set of grafana dashboards for monitoring hub usage across all hubs on a cluster.
The support chart **must** be deployed before trying to install the dashboards, since the support chart installs prometheus and grafana.

**Command line usage:**

```bash
usage: python deployer deploy-grafana-dashboards [-h] cluster_name

positional arguments:
  cluster_name  The name of the cluster to perform actions on

optional arguments:
  -h, --help    show this help message and exit
```

### `use-cluster-credentials`

This function provides quick command line/`kubectl` access to a cluster.
Running this command will spawn a new shell with all the appropriate environment variables and `KUBECONFIG` contexts set to allow `kubectl` commands to be run against a cluster.
It uses the deployer credentials saved in the repository and does not authenticate a user with their own profile - it will be a service account and may have different permissions depending on the cloud provider.
Remember to close the opened shell after you've finished by using the `exit` command or typing `Ctrl`+`D`/`Cmd`+`D`.

**Command line usage:**

```bash
usage: python deployer use-cluster-credentials [-h] cluster_name

positional arguments:
  cluster_name  The name of the cluster to perform actions on

optional arguments:
  -h, --help    show this help message and exit
```


### `generate-helm-upgrade-jobs`

This function consumes a list of files that have been added or modified, and from that deduces which hubs on which clusters require a helm upgrade, and whether the support chart also needs upgrading.
It constructs a human-readable table of the hubs that will be upgraded as a result of the changed files.

This function is primarily used in our CI/CD infrastructure and, on top of the human-readable output, JSON objects are also set as outputs that can be interpreted by GitHub Actions as matrix jobs.
This allows us to optimise and parallelise the automatic deployment of our hubs.

**Command line usage:**

```bash
usage: python deployer generate-helm-upgrade-jobs [-h] [filepaths]

positional arguments:
  filepaths   A singular or space-delimited list of added or modified filepaths in the repo

optional arguments:
  -h, --help  show this help message and exit
```

### `run-hub-health-check`

This function checks that a given hub is healthy by:

1. Creating a user
2. Starting a server
3. Executing a Notebook on that server

For daskhubs, there is an optional check to verify that the user can scale dask workers.

**Command line usage:**

```bash
usage: python deployer run-hub-health-check [-h] [--check-dask-scaling] cluster_name hub_name

positional arguments:
  cluster_name          The name of the cluster to perform actions on
  hub_name              The hub to run health checks against.

optional arguments:
  -h, --help            show this help message and exit
  --check-dask-scaling  For daskhubs, optionally check that dask workers can be scaled
```

## Debugging helpers

We also have some debug helpers commands that can be invoked as subcommands
of `python3 -m deployer.debug`. These are primarily helpful for manual actions
when debugging issues (during setup or an outage), or when taking down a hub.
`python3 -m deployer.debug --help` is the authoritative help document for all
the options available, but they are also documented here.

All these commands take a cluster and hub name as parameters, and perform appropriate
authentication before performing their function.

### `component-logs`

This subcommand displays live updating logs of a particular core component of a particular
JupyterHub on a given cluster. You can pass `--no-follow` to provide just
logs upto the current point in time and then stop. If the component pod has restarted
due to an error, you can pass `--previous` to look at the logs of the pod
prior to the last restart.

```
Usage: python3 deployer.debug component-logs [OPTIONS] CLUSTER_NAME HUB_NAME
                               COMPONENT:[hub|proxy|dask-gateway-api|dask-
                               gateway-controller|dask-gateway-traefik]

  Display logs from a particular component on a hub on a cluster

Arguments:
  CLUSTER_NAME                    Name of cluster to operate on  [required]
  HUB_NAME                        Name of hub to operate on  [required]
  COMPONENT:[hub|proxy|dask-gateway-api|dask-gateway-controller|dask-gateway-traefik]
                                  Component to display logs of  [required]

Options:
  --follow / --no-follow      Live update new logs as they show up  [default:
                              True]

  --previous / --no-previous  If component pod has restarted, show logs from
                              just before the restart  [default: False]

  --help                      Show this message and exit.
```

### `user-logs`

This subcommand displays live updating logs of a prticular user on a hub if
it is currently running. If sidecar containers are present (such as per-user db),
they are ignored and only the notebook logs are provided. You can pass
`--no-follow` to provide logs upto the current point only.

```
Usage: python3 deployer.debug user-logs [OPTIONS] CLUSTER_NAME HUB_NAME USERNAME

  Display logs from the notebook pod of a given user

Arguments:
  CLUSTER_NAME  Name of cluster to operate on  [required]
  HUB_NAME      Name of hub to operate on  [required]
  USERNAME      Name of the JupyterHub user to get logs for  [required]

Options:
  --follow / --no-follow  Live update new logs as they show up  [default:
                          True]

  --help                  Show this message and exit.
```

### `exec-hub-shell`

This subcommand gives you an interactive shell on the hub pod itself, so you
can poke around to see what's going on. Particularly useful if you want to peek
at the hub db with the `sqlite` command.

```
Usage: python3 deployer.debug exec-hub-shell [OPTIONS] CLUSTER_NAME HUB_NAME

  Pop an interactive shell in the hub pod

Arguments:
  CLUSTER_NAME  Name of cluster to operate on  [required]
  HUB_NAME      Name of hub to operate on  [required]

Options:
  --help  Show this message and exit.
```

### `exec-homes-shell`

This subcommand gives you a shell with the home directories of all the
users on the given hub in the given cluster mounted under `/home`.
Very helpful when doing (rare) manual operations on user home directories,
such as renames.

When you exit the shell, the temporary pod spun up is removed.

```bash
Usage: debug.py exec-homes-shell [OPTIONS] CLUSTER_NAME HUB_NAME

  Pop an interactive shell with the home directories of the given hub
  mounted on /home

Arguments:
  CLUSTER_NAME  Name of cluster to operate on  [required]
  HUB_NAME      Name of hub to operate on  [required]

Options:
  --help  Show this message and exit.
```

## Sub-scripts

This section describes the utility scripts that are present in the `deployer` module, what is their purpose, and their command line usage.\

**Note:** The `deployer` sub-scripts must currently be invoked from the root of this repository, i.e.:

```bash
$ pwd
[...]/infrastructure/deployer
$ cd .. && pwd
[...]/infrastructure
$ python deployer/[sub-script].py
```

### `cilogon_app`

This is a helper script that can create/update/get/delete CILogon clients using the 2i2c administrative client provided by CILogon.

**Command line usage:**

```bash
usage: cilogon_app.py [-h] {create,update,get,get-all,delete} ...

A command line tool to create/update/delete CILogon clients.

positional arguments:
  {create,update,get,get-all,delete}
                        Available subcommands
    create              Create a CILogon client
    update              Update a CILogon client
    get                 Retrieve details about an existing CILogon client
    get-all             Retrieve details about an existing CILogon client
    delete              Delete an existing CILogon client

optional arguments:
  -h, --help            show this help message and exit
```

### `update_central_grafana_datasources.py`

Ensures that the central grafana at https://grafana.pilot.2i2c.cloud is configured to use as datasource the authenticated prometheus instances of all the clusters that we run.

**Command line usage:**

```bash
usage: update_central_grafana_datasources.py [-h] [cluster_name]

A command line tool to update Grafana datasources.

positional arguments:
  cluster_name  The name of the cluster where the Grafana lives

optional arguments:
  -h, --help    show this help message and exit
```

## Running Tests

To execute tests on the `deployer`, you will need to install the development requirements and then invoke `pytest` from the root of the repository.

```bash
$ pwd
[...]/infrastructure/deployer
$ cd .. && pwd
[...]/infrastructure
$ pip install -r deployer/dev-requirements.txt
$ python -m pytest -vvv
```
