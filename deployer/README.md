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

## The directory structure of the deployer package

The deployer has the following directory structure:

```bash
├── README.md
├── __init__.py
├── __main__.py
├── cli_app.py
├── commands
├── health_check_tests
├── infra_components
├── keys
└── utils
```

### The `cli_app.py` file

The `cli_app.py` file is the file that contains the main `deployer` typer app and all of the main sub-apps "attached" to it, each corresponding to a `deployer` sub-command. These apps are used throughout the codebase.

### The `__main__.py` file

The `__main__.py` file is the main file that gets executed when the deployer is called.
If you are adding any sub-command functions, you **must** import them in this file for them to be picked up by the package.

### The `infra_components` directory

This is the directory where the files that define the `Hub` and `Cluster` classes are stored. These files are imported and used throughout the deployer's codebase to emulate these objects programmatically.

```bash
├── infra_components
│   ├── cluster.py
│   └── hub.py
```

### The `utils` directory
This is where utility functions are stored. They are to be imported and used throughout the entire codebase of the deployer.

```bash
└── utils
    ├── file_acquisition.py
    └── rendering.py
```

### The `commands` directory

This is the directory where all of the code related to the main `deployer` sub-commands is stored.

Each sub-commands's functions are stored:
- either in a single Python file where such thing was straight-forward
- or in a directory that matches the name of the sub-command, if it's more complex and requires additional helper files.

The `deployer.py` file is the main file, that contains all of the commands registered directly on the `deployer` main typer app, that could not or were not yet categorized in sub-commands.

```bash
── commands
│   ├── cilogon.py
│   ├── debug.py
│   ├── deployer.py
│   ├── exec
│   │   ├── cloud.py
│   │   └── infra_components.py
│   ├── generate
│   │   ├── __init__.py
│   │   ├── billing
│   │   │   ├── cost_table.py
│   │   │   ├── importers.py
│   │   │   └── outputers.py
│   │   ├── dedicated_cluster
│   │   │   ├── aws.py
│   │   │   ├── common.py
│   │   │   ├── dedicate_cluster_app.py
│   │   │   └── gcp.py
│   │   └── helm_upgrade
│   │   |   ├── decision.py
│   │   |   └── jobs.py
|   |   └── resource_allocation
│   │       ├── daemonset_requests.py
│   │       ├── daemonset_requests.yaml
│   │       ├── generate_choices.py
│   │       ├── instance_capacities.py
│   │       ├── instance_capacities.yaml
│   │       ├── node-capacity-info.json
│   │       ├── resource_allocation_app.py
│   │       └── update_nodeinfo.py
│   ├── grafana
│   │   ├── central_grafana.py
│   │   ├── deploy_dashboards.py
│   │   ├── tokens.py
│   │   └── utils.py
│   ├── validate
│   │   ├── cluster.schema.yaml
│   │   └── config.py
│   └── verify_backups.py
```

### The `health_check_tests` directory

This directory contains the tests and assets used by them. It is called by `deployer run-hub-health-check` command to determine whether a hub should be marked as healthy or not.

```bash
├── health_check_tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test-notebooks
│   │   ├── basehub
│   │   │   └── simple.ipynb
│   │   └── daskhub
│   │       ├── dask_test_notebook.ipynb
│   │       └── scale_dask_workers.ipynb
│   └── test_hub_health.py
```

## The deployer's main sub-commands
This section descripts some of the subcommands the `deployer` can carry out.

**Command line usage:**

```bash
 Usage: deployer [OPTIONS] COMMAND [ARGS]...                                                                                                                                                 
                                                                                                                                                                                             
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                                                                                   │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                                                                            │
│ --help                        Show this message and exit.                                                                                                                                 │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cilogon-client            Manage cilogon clients for hubs' authentication.                                                                                                                │
│ config                    Get refined information from the config folder.                                                                                                                 │
│ debug                     Debug issues by accessing different components and their logs                                                                                                   │
│ decrypt-age               Decrypt secrets sent to `support@2i2c.org` via `age`                                                                                                            │
│ deploy                    Deploy one or more hubs in a given cluster                                                                                                                      │
│ deploy-support            Deploy support components to a cluster                                                                                                                          │
│ exec                      Execute a shell in various parts of the infra. It can be used for poking around, or debugging issues.                                                           │
│ generate                  Generate various types of assets. It currently supports generating files related to billing, new dedicated clusters, helm upgrade strategies and resource       │
│                           allocation.                                                                                                                                                     │
│ grafana                   Manages Grafana related workflows.                                                                                                                              │
│ run-hub-health-check      Run a health check on a given hub on a given cluster. Optionally check scaling of dask workers if the hub is a daskhub.                                         │
│ transform                 Programmatically transform datasets, such as cost tables for billing purposes.                                                                                  │
│ use-cluster-credentials   Pop a new shell or execute a command after authenticating to the given cluster using the deployer's credentials                                                 │
│ validate                  Validate configuration files such as helm chart values and cluster.yaml files.                                                                                  │
│ verify-backups            Verify backups of home directories have been successfully created, and old backups have been cleared out.                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Standalone sub-commands related to deployment

These deployment related commands are all stored in `deployer/commands/deployer.py` file and are registered on the main `deployer` typer app.

#### `deploy`

This function is used to deploy changes to a hub (or list of hubs), or install it if it does not yet exist.
It takes a name of a cluster and a name of a hub (or list of names) as arguments, gathers together the config files under `/config/clusters` that describe the individual hub(s), and runs `helm upgrade` with these files passed as `--values` arguments.


#### `deploy-support`

This function deploys changes to the support helm chart on a cluster, or installs it if it's not already present.
This command only needs to be run once per cluster, not once per hub.

#### `use-cluster-credentials`

This function provides quick command line/`kubectl` access to a cluster.
Running this command will spawn a new shell with all the appropriate environment variables and `KUBECONFIG` contexts set to allow `kubectl` commands to be run against a cluster.
It uses the deployer credentials saved in the repository and does not authenticate a user with their own profile - it will be a service account and may have different permissions depending on the cloud provider.
Remember to close the opened shell after you've finished by using the `exit` command or typing `Ctrl`+`D`/`Cmd`+`D`.

#### `run-hub-health-check`

This function checks that a given hub is healthy by:

1. Creating a user
2. Starting a server
3. Executing a Notebook on that server

For daskhubs, there is an optional check to verify that the user can scale dask workers.


#### Support helper tools: `decrypt-age`

Decrypts information sent to 2i2c by community representatives using [age](https://age-encryption.org/) according to instructions in [2i2c documentation](https://docs.2i2c.org/en/latest/support.html?highlight=decrypt#send-us-encrypted-content).

### The `config` sub-command

This deployer sub-command provides misc information.

#### `config get-clusters`

This function prints a sorted list of clusters, optionally filtered by the
`--provider` flag.

### The `generate` sub-command

This deployer sub-command is used to generate various types of file assets. Currently, it can generate the cost billing table, initial cluster infrastructure files and the helm upgrade jobs.

#### `generate helm-upgrade-jobs`

This function consumes a list of files that have been added or modified, and from that deduces which hubs on which clusters require a helm upgrade, and whether the support chart also needs upgrading.
It constructs a human-readable table of the hubs that will be upgraded as a result of the changed files.

This function is primarily used in our CI/CD infrastructure and, on top of the human-readable output, JSON objects are also set as outputs that can be interpreted by GitHub Actions as matrix jobs.
This allows us to optimise and parallelise the automatic deployment of our hubs.


#### `generate dedicated-cluster`
This generate sub-command can be used to create the initial files needed for a new cluster on GCP or AWS.

##### `generate dedicated-cluster aws`

This function generates the required files for an AWS cluster based on a few input fields,
the name of the cluster, the region where the cluster will be deployed and whether the hub deployed there would need dask or not.

  Generates:
  - an eksctl jsonnet file
  - a .tfvars file
  - An ssh-key (the private part is encrypted)
  - cluster configuration files:
    - `config/<cluster_name>/cluster.yaml`
    - `config/<cluster_name>/support.values.yaml`
    - `config/<cluster_name>/enc-support.secret.values.yaml`

The files are generated based on the jsonnet templates in:
  - (`eksctl/template.json`)[https://github.com/2i2c-org/infrastructure/blob/main/eksctl/template.jsonnet]
  - (`terraform/aws/projects/basehub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/main/terraform/aws/projects/basehub-template.tfvars]


##### `generate dedicated-cluster gcp`

This function generates the infrastructure terraform file and the configuration directory
for a GCP cluster.

  Generates:
    - infrastructure file:
      - `terraform/gcp/projects/<cluster_name>.tfvars`
    - cluster configuration files:
      - `config/<cluster_name>/cluster.yaml`
      - `config/<cluster_name>/support.values.yaml`
      - `config/<cluster_name>/enc-support.secret.values.yaml`

  The files are generated based on the content in a set of template files and a few input fields:
    - `cluster_name` - the name of the cluster
    - `cluster_region`- the region where the cluster will be deployed
    - `project_id` - the project ID of the GCP project
    - `hub_name` - the name of the first hub which will be deployed in the cluster (usually `staging`)

The templates have a set of default features and define some opinionated characteristics for the cluster.
These defaults are described in each file template.

  The infrastructure terraform config is generated based on the terraform templates in:
    - (`terraform/basehub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/main/terraform/gcp/projects/basehub-template.tfvars]
    - (`terraform/daskhub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/main/terraform/gcp/projects/daskhub-template.tfvars]
  The cluster configuration directory is generated based on the templates in:
    - (`config/clusters/templates/gcp`)[https://github.com/2i2c-org/infrastructure/blob/main/config/clusters/templates/gcp]

#### `generate resource-allocation`

This sub-command can be used to generate the resource allocation choices for given instance type and a given optimization strategy.

##### `generate resource-allocation choices`
This generates a custom number of resource allocation choices for a certain instance type, depending on a certain chosen strategy that can be used in the profile list of a hub.

##### `generate resource-allocation daemonset-requests`
Updates `daemonset_requests.yaml` with an individual cluster's DaemonSets' requests summarized.

Only DaemonSet's with running pods are considered, and GPU related DaemonSets (with "nvidia" in the name) are also ignored.

To run this command for all clusters, `xargs` can be used like this:

    deployer config get-clusters | xargs -I {} deployer generate resource-allocation daemonset-requests {}

##### `generate resource-allocation instance-capacities`
Updates `instance_capacities.yaml` with an individual cluster's running instance types' total and allocatable capacity.

To run this command for all clusters, `xargs` can be used like this:

    deployer config get-clusters | xargs -I {} deployer generate resource-allocation instance-capacities {}

##### `generate resource-allocation node-info-update`
This updates the json file `node-capacity-info.json` with info about the capacity of a node of a certain type. This file is then used for generating the resource choices.

### The `grafana` sub-command
This deployer sub-command manages all of the available functions related to Grafana.

#### `grafana deploy-dashboards`

This function uses [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) to create a set of grafana dashboards for monitoring hub usage across all hubs on a cluster.
The support chart **must** be deployed before trying to install the dashboards, since the support chart installs prometheus and grafana.

#### `grafana new-token`

This function uses the admin credentials located in `helm-charts/support/enc-support.secret.values.yaml` to check if a [Grafana Service Account](https://grafana.com/docs/grafana/latest/administration/service-accounts/) named `deployer` exists for a cluster's Grafana, and creates it if it doesn't.
For this service account, it then generates a Grafana token named `deployer`.
This token will be used by the [`deploy-grafana-dashboards` workflow](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-grafana-dashboards.yaml) to authenticate with [Grafana’s HTTP API](https://grafana.com/docs/grafana/latest/developers/http_api/).

```{note}
More about HTTP vs REST APIs at https://www.programsbuzz.com/article/what-difference-between-rest-api-and-http-api.
```
and deploy some default grafana dashboards for JupyterHub using [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).
If a token with this name already exists, it will show whether or not the token is expired
and wait for cli input about whether to generate a new one or not.

The Grafana token is then stored encrypted inside the `enc-grafana-token.secret.yaml` file in the cluster's configuration directory.
If such a file doesn't already exist, it will be created by this function.

  Generates:
  - an `enc-grafana-token.secret.yaml` file if not already present

  Updates:
  - the content of `enc-grafana-token.secret.yaml` with the new token if one already existed

#### The `grafana central-ds` sub-command
This is a sub-command meant to help engineers to programmatically manage the datasources registered in the 2i2c central Grafana at https://grafana.pilot.2i2c.cloud.

##### `grafana central-ds add`
Adds a new cluster as a datasource to the central Grafana.

##### `grafana central-ds remove`
Removes a datasource from the central Grafana. In the unlikely case, the datasource has a different name than the cluster's name, pass it through the optional `datasource-name` flag.

##### `grafana central-ds get-add-candidates`
Gets the clusters that are in the infrastructure repository but are NOT registered in central grafana as datasources. Usually this happens when a new clusters was added, but its prometheus server was not mapped to a datasource of the central 2i2c Grafana. This list can then be used to know which datasources to add.

##### `grafana central-ds get-rm-candidates`
Gets the list of datasources that are registered in central grafana but are NOT in the list of clusters in the infrastructure repository. Usually this happens when a clusters was decommissioned, but its prometheus server was not removed from the datasources of the central 2i2c Grafana. This list can then be used to know which datasources to remove.

### The `transform` sub-command

This sub-command can be used to transform various datasets.

#### `transform cost-table`

This is a sub-command meant to help engineers transform cost tables generated by cloud vendors into the format required by our fiscal sponsor in order for them to bill our communities.
This transformation is automated to avoid copy-paste errors from one CSV file to another.
These transformations happen locally and another CSV file is outputted to the local directory, which then needs to be manually handed over to CS&S staff.

##### `transform cost-table aws`

Transforms a cost table generated in the AWS UI into the correct format.

##### `transform cost-table gcp`

Transforms a cost table generated in the GCP UI into the correct format.

### The `validate` sub-command

This function is used to validate the values files for each of our hubs against their helm chart's values schema.
This allows us to validate that all required values are present and have the correct type before we attempt a deployment.

### The `cilogon-client` sub-command for CILogon OAuth client management
Deployer sub-command for managing CILogon clients for 2i2c hubs.

#### `cilogon-client create/delete/get/get-all/update/cleanup`

create/delete/get/get-all/update/cleanup CILogon clients using the 2i2c administrative client provided by CILogon.

### The `exec` sub-command for executing shells and debugging commands

This deployer `exec` sub-command can be used to
exec a shell in various parts of the infrastructure.
It can be used for poking around, or debugging issues.

These are primarily helpful for manual actions when debugging issues (during
setup or an outage), or when taking down a hub. 

All these commands take a cluster and hub name as parameters, and perform appropriate
authentication before performing their function.

#### `exec hub`

This subcommand gives you an interactive shell on the hub pod itself, so you
can poke around to see what's going on. Particularly useful if you want to peek
at the hub db with the `sqlite` command.

#### `exec homes`

This subcommand gives you a shell with the home directories of all the
users on the given hub in the given cluster mounted under `/home`.
Very helpful when doing (rare) manual operations on user home directories,
such as renames.

When you exit the shell, the temporary pod spun up is removed.

#### `exec root-homes`

Similar to `exec homes` but mounts the _entire_ NFS filesystem to `/root-homes`.
You can optionally mount a secondary NFS share if required, which is useful when migrating data across servers.

#### `exec aws`

This sub-command can exec into a shell with appropriate AWS credentials (including MFA).

#### `exec debug`

This sub-command is useful for debugging.

##### `exec debug component-logs`

This subcommand displays live updating logs of a particular core component of a particular
JupyterHub on a given cluster. You can pass `--no-follow` to provide just
logs upto the current point in time and then stop. If the component pod has restarted
due to an error, you can pass `--previous` to look at the logs of the pod
prior to the last restart.

##### `exec debug user-logs`

This subcommand displays live updating logs of a prticular user on a hub if
it is currently running. If sidecar containers are present (such as per-user db),
they are ignored and only the notebook logs are provided. You can pass
`--no-follow` to provide logs upto the current point only.

##### `exec debug start-docker-proxy`

Building docker images locally can be *extremely* slow and frustrating. We run a central docker daemon
in our 2i2c cluster that can be accessed via this command, and speeds up image builds quite a bit!
Once you run this command, run `export DOCKER_HOST=tcp://localhost:23760` in another terminal to use the faster remote
docker daemon.

## Running Tests

To execute tests on the `deployer`, you will need to install the development requirements and then invoke `pytest` from the root of the repository.

```bash
$ pwd
[...]/infrastructure/deployer
$ cd .. && pwd
[...]/infrastructure
$ pip install -e .[dev]
$ python -m pytest -vvv
```
