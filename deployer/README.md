# The `deployer` module

## Summary

The `deployer` is a Python module that automates various tasks that 2i2c undertake to manage 2i2c-hosted JupyterHubs.

## Installing the deployer

The deployer is packaged as a local package (not published on PyPI). You can
use `pip` to install it.
You may wish to create a virtual environment using `venv` or `conda` first.

```bash
pip install --editable .
```

The `--editable` makes sure any changes you make to the deployer itself are
immediately effected.

## Deployment Commands


This section descripts all the deployment related subcommands the `deployer` can carry out and their commandline parameters.


**Command line usage:**

```bash
 Usage: deployer [OPTIONS] COMMAND [ARGS]...                                                                            
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                              │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.       │
│ --help                        Show this message and exit.                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ component-logs              Display logs from a particular component on a hub on a cluster                           │
│ deploy                      Deploy one or more hubs in a given cluster                                               │
│ deploy-grafana-dashboards   Deploy JupyterHub dashboards to grafana set up in the given cluster                      │
│ deploy-support              Deploy support components to a cluster                                                   │
│ exec-homes-shell            Pop an interactive shell with the home directories of the given hub mounted on /home     │
│ exec-hub-shell              Pop an interactive shell in the hub pod                                                  │
│ generate-helm-upgrade-jobs  Analyse added or modified files from a GitHub Pull Request and decide which clusters     │
│                             and/or hubs require helm upgrades to be performed for their *hub helm charts or the      │
│                             support helm chart.                                                                      │
│ run-hub-health-check        Run a health check on a given hub on a given cluster. Optionally check scaling of dask   │
│                             workers if the hub is a daskhub.                                                         │
│ use-cluster-credentials     Pop a new shell authenticated to the given cluster using the deployer's credentials      │
│ user-logs                   Display logs from the notebook pod of a given user                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `deploy`

This function is used to deploy changes to a hub (or list of hubs), or install it if it does not yet exist.
It takes a name of a cluster and a name of a hub (or list of names) as arguments, gathers together the config files under `/config/clusters` that describe the individual hub(s), and runs `helm upgrade` with these files passed as `--values` arguments.

**Command line usage:**

```bash
 Usage: deployer deploy [OPTIONS] CLUSTER_NAME [HUB_NAME]                                                               
                                                                                                                        
 Deploy one or more hubs in a given cluster                                                                             
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT        Name of cluster to operate on [default: None] [required]                          │
│      hub_name          [HUB_NAME]  Name of hub to operate deploy. Omit to deploy all hubs on the cluster             │
│                                    [default: None]                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config-path                 TEXT  File to read secret deployment config from                                       │
│                                     [default: shared/deployer/enc-auth-providers-credentials.secret.yaml]            │
│ --dask-gateway-version        TEXT  Version of dask-gateway to install CRDs for [default: v2022.10.0]                │
│ --help                              Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `validate`

This function is used to validate the values files for each of our hubs against their helm chart's values schema.
This allows us to validate that all required values are present and have the correct type before we attempt a deployment.

**Command line usage:**

```bash
 Usage: deployer validate [OPTIONS] CLUSTER_NAME HUB_NAME                                                               
                                                                                                                        
 Validate cluster.yaml and non-encrypted helm config for given hub                                                      
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `deploy-support`

This function deploys changes to the support helm chart on a cluster, or installs it if it's not already present.
This command only needs to be run once per cluster, not once per hub.

**Command line usage:**

```bash
 Usage: deployer deploy-support [OPTIONS] CLUSTER_NAME                                                                  
                                                                                                                        
 Deploy support components to a cluster                                                                                 
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --cert-manager-version        TEXT  Version of cert-manager to install [default: v1.8.2]                             │
│ --help                              Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `deploy-grafana-dashboards`

This function uses [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) to create a set of grafana dashboards for monitoring hub usage across all hubs on a cluster.
The support chart **must** be deployed before trying to install the dashboards, since the support chart installs prometheus and grafana.

**Command line usage:**

```bash
 Usage: deployer deploy-grafana-dashboards [OPTIONS] CLUSTER_NAME                                                       
                                                                                                                        
 Deploy JupyterHub dashboards to grafana set up in the given cluster                                                    
 Grafana dashboards and deployment mechanism are maintained at https://github.com/jupyterhub/grafana-dashboards         
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `use-cluster-credentials`

This function provides quick command line/`kubectl` access to a cluster.
Running this command will spawn a new shell with all the appropriate environment variables and `KUBECONFIG` contexts set to allow `kubectl` commands to be run against a cluster.
It uses the deployer credentials saved in the repository and does not authenticate a user with their own profile - it will be a service account and may have different permissions depending on the cloud provider.
Remember to close the opened shell after you've finished by using the `exit` command or typing `Ctrl`+`D`/`Cmd`+`D`.

**Command line usage:**

```bash
 Usage: deployer use-cluster-credentials [OPTIONS] CLUSTER_NAME                                                         
                                                                                                                        
 Pop a new shell authenticated to the given cluster using the deployer's credentials                                    
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


### `generate-helm-upgrade-jobs`

This function consumes a list of files that have been added or modified, and from that deduces which hubs on which clusters require a helm upgrade, and whether the support chart also needs upgrading.
It constructs a human-readable table of the hubs that will be upgraded as a result of the changed files.

This function is primarily used in our CI/CD infrastructure and, on top of the human-readable output, JSON objects are also set as outputs that can be interpreted by GitHub Actions as matrix jobs.
This allows us to optimise and parallelise the automatic deployment of our hubs.

**Command line usage:**

```bash
 Usage: deployer generate-helm-upgrade-jobs [OPTIONS] CHANGED_FILEPATHS                                                 
                                                                                                                        
 Analyse added or modified files from a GitHub Pull Request and decide which clusters and/or hubs require helm upgrades 
 to be performed for their *hub helm charts or the support helm chart.                                                  
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    changed_filepaths      TEXT  Space delimited list of files that have changed [default: None] [required]         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `run-hub-health-check`

This function checks that a given hub is healthy by:

1. Creating a user
2. Starting a server
3. Executing a Notebook on that server

For daskhubs, there is an optional check to verify that the user can scale dask workers.

**Command line usage:**

```bash
 Usage: deployer run-hub-health-check [OPTIONS] CLUSTER_NAME HUB_NAME                                                   
                                                                                                                        
 Run a health check on a given hub on a given cluster. Optionally check scaling of dask workers if the hub is a         
 daskhub.                                                                                                               
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --check-dask-scaling    --no-check-dask-scaling      Check that dask workers can be scaled                           │
│                                                      [default: no-check-dask-scaling]                                │
│ --help                                               Show this message and exit.                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Debugging helpers

We also have some debug helpers commands that can be invoked as subcommands.
These are primarily helpful for manual actions when debugging issues (during
setup or an outage), or when taking down a hub. 

All these commands take a cluster and hub name as parameters, and perform appropriate
authentication before performing their function.

### `component-logs`

This subcommand displays live updating logs of a particular core component of a particular
JupyterHub on a given cluster. You can pass `--no-follow` to provide just
logs upto the current point in time and then stop. If the component pod has restarted
due to an error, you can pass `--previous` to look at the logs of the pod
prior to the last restart.

```
 Usage: deployer component-logs [OPTIONS] CLUSTER_NAME HUB_NAME                                                         
                                COMPONENT:{hub|proxy|dask-gateway-api|dask-                                             
                                gateway-controller|dask-gateway-traefik}                                                
                                                                                                                        
 Display logs from a particular component on a hub on a cluster                                                         
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT                                           Name of cluster to operate on [default: None]  │
│                                                                       [required]                                     │
│ *    hub_name          TEXT                                           Name of hub to operate on [default: None]      │
│                                                                       [required]                                     │
│ *    component         COMPONENT:{hub|proxy|dask-gateway-api|dask-ga  Component to display logs of [default: None]   │
│                        teway-controller|dask-gateway-traefik}         [required]                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --follow      --no-follow        Live update new logs as they show up [default: follow]                              │
│ --previous    --no-previous      If component pod has restarted, show logs from just before the restart              │
│                                  [default: no-previous]                                                              │
│ --help                           Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `user-logs`

This subcommand displays live updating logs of a prticular user on a hub if
it is currently running. If sidecar containers are present (such as per-user db),
they are ignored and only the notebook logs are provided. You can pass
`--no-follow` to provide logs upto the current point only.

```
 Usage: deployer user-logs [OPTIONS] CLUSTER_NAME HUB_NAME USERNAME                                                     
                                                                                                                        
 Display logs from the notebook pod of a given user                                                                     
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
│ *    username          TEXT  Name of the JupyterHub user to get logs for [default: None] [required]                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --follow    --no-follow      Live update new logs as they show up [default: follow]                                  │
│ --help                       Show this message and exit.                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

### `exec-hub-shell`

This subcommand gives you an interactive shell on the hub pod itself, so you
can poke around to see what's going on. Particularly useful if you want to peek
at the hub db with the `sqlite` command.

```
 Usage: deployer exec-hub-shell [OPTIONS] CLUSTER_NAME HUB_NAME                                                         
                                                                                                                        
 Pop an interactive shell in the hub pod                                                                                
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `exec-homes-shell`

This subcommand gives you a shell with the home directories of all the
users on the given hub in the given cluster mounted under `/home`.
Very helpful when doing (rare) manual operations on user home directories,
such as renames.

When you exit the shell, the temporary pod spun up is removed.

```bash
 Usage: deployer exec-homes-shell [OPTIONS] CLUSTER_NAME HUB_NAME                                                       
                                                                                                                        
 Pop an interactive shell with the home directories of the given hub mounted on /home                                   
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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
