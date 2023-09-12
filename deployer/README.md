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
├── infra_components
├── keys
├── tests
└── utils
```

### The `cli_app.py` file
The `cli_app.py` file is the file that contains the main `deployer` typer app and all of the main sub-apps "attached" to it, each corresponding to a `deployer` sub-command. These apps are used throughout the codebase.

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
- either in a single Python file that ends in `_cmd` or `_commands`
- or in a directory that matches the name of the sub-command, if it is more complex and required additional helper files.

The `deployer.py` file is the main file, that contains all of the commands registered directly on the `deployer` main typer app, that could not or were not yet categorized in sub-commands.

```bash
├── commands
│   ├── cilogon_client_cmd.py
│   ├── deployer.py
│   ├── exec
│   │   ├── debug_app_and_commands.py
│   │   └── shell
│   │       ├── app.py
│   │       ├── cloud_commands.py
│   │       └── infra_components_commands.py
│   ├── generate
│   │   ├── __init__.py
│   │   ├── billing
│   │   │   ├── cost_table_cmd.py
│   │   │   ├── importers.py
│   │   │   └── outputers.py
│   │   ├── dedicated_cluster
│   │   │   ├── aws_commands.py
│   │   │   ├── common.py
│   │   │   ├── dedicate_cluster_app.py
│   │   │   └── gcp_commands.py
│   │   └── helm_upgrade
│   │       ├── decision.py
│   │       └── jobs_cmd.py
│   ├── grafana
│   │   ├── central_grafana.py
│   │   ├── deploy_dashboards_cmd.py
│   │   ├── tokens_cmd.py
│   │   └── utils.py
│   └── validate
│       ├── cluster.schema.yaml
│       └── config_cmd.py
```

### The `tests` directory

This directory contains the tests and assets used by these tests and called by `deployer run-hub-health-check` command to determine whether a hub should be marked as healthy or not.

```bash
├── tests
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

## The deployer's main sub-commands commandline usage
This section descripts all the subcommands the `deployer` can carry out and their commandline parameters.

**Command line usage:**

```bash
                                                                                                                        
 Usage: deployer [OPTIONS] COMMAND [ARGS]...                                                                            
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion        [bash|zsh|fish|powershell|pwsh]  Install completion for the specified shell.             │
│                                                              [default: None]                                         │
│ --show-completion           [bash|zsh|fish|powershell|pwsh]  Show completion for the specified shell, to copy it or  │
│                                                              customize the installation.                             │
│                                                              [default: None]                                         │
│ --help                                                       Show this message and exit.                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cilogon-client           Manage cilogon clients for hubs' authentication.                                            │
│ decrypt-age              Decrypt secrets sent to `support@2i2c.org` via `age`                                        │
│ deploy                   Deploy one or more hubs in a given cluster                                                  │
│ deploy-support           Deploy support components to a cluster                                                      │
│ exec                     Execute a shell in various parts of the infra. It can be used for poking around, or         │
│                          debugging issues.                                                                           │
│ generate                 Generate various types of assets. It currently supports generating files related to billing │
│                          or new, dedicated clusters.                                                                 │
│ grafana                  Manages Grafana related workflows.                                                          │
│ run-hub-health-check     Run a health check on a given hub on a given cluster. Optionally check scaling of dask      │
│                          workers if the hub is a daskhub.                                                            │
│ use-cluster-credentials  Pop a new shell or execute a command after authenticating to the given cluster using the    │
│                          deployer's credentials                                                                      │
│ validate                 Validate configuration files such as helm chart values and cluster.yaml files.              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Standalone sub-commands related to deployment

These deployment related commands are all stored in `deployer/commands/deployer.py` file and are registered on the main `deployer` typer app.

#### `deploy`

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
│ --dask-gateway-version        TEXT  Version of dask-gateway to install CRDs for [default: 2023.1.0]                  │
│ --debug                             When present, the `--debug` flag will be passed to the `helm upgrade` command.   │
│ --dry-run                           When present, the `--dry-run` flag will be passed to the `helm upgrade` command. │
│ --help                              Show this message and exit.                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `deploy-support`

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

#### `use-cluster-credentials`

This function provides quick command line/`kubectl` access to a cluster.
Running this command will spawn a new shell with all the appropriate environment variables and `KUBECONFIG` contexts set to allow `kubectl` commands to be run against a cluster.
It uses the deployer credentials saved in the repository and does not authenticate a user with their own profile - it will be a service account and may have different permissions depending on the cloud provider.
Remember to close the opened shell after you've finished by using the `exit` command or typing `Ctrl`+`D`/`Cmd`+`D`.

**Command line usage:**

```bash
                                                                                    
 Usage: deployer use-cluster-credentials [OPTIONS] CLUSTER_NAME COMMANDLINE         
                                                                                    
 Pop a new shell or execute a command after authenticating to the given cluster     
 using the deployer's credentials                                                   
                                                                                    
╭─ Arguments ──────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None]       │
│                              [required]                                          │
│ *    commandline       TEXT  Optional shell command line to run after            │
│                              authenticating to this cluster                      │
│                              [default: None]                                     │
│                              [required]                                          │
╰──────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                      │
╰──────────────────────────────────────────────────────────────────────────────────╯

```

#### `run-hub-health-check`

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

#### Support helper tools: `decrypt-age`

Decrypts information sent to 2i2c by community representatives using [age](https://age-encryption.org/) according to instructions in [2i2c documentation](https://docs.2i2c.org/en/latest/support.html?highlight=decrypt#send-us-encrypted-content).

**Command line usage:**
```
 Usage: deployer decrypt-age [OPTIONS]                                                                                  
                                                                                                                        
 Decrypt secrets sent to `support@2i2c.org` via `age`                                                                   
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --encrypted-file-path        TEXT  Path to age-encrypted file sent by user. Leave empty to read from stdin.          │
│ --help                             Show this message and exit.                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### The `generate` sub-command

This deployer sub-command is used to generate various types of file assets. Currently, it can generate the cost billing table, initial cluster infrastructure files and the helm upgrade jobs.

**Command line usage:**

```bash
                                                                                                                       
 Usage: deployer generate [OPTIONS] COMMAND [ARGS]...                                                                   
                                                                                                                        
 Generate various types of assets. It currently supports generating files related to billing or new, dedicated          
 clusters.                                                                                                              
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cost-table         Generate table with cloud costs for all GCP projects we pass costs through for.                   │
│ dedicated-cluster  Generate the initial files needed for a new cluster on GCP or AWS.                                │
│ helm-upgrade-jobs  Analyze added or modified files from a GitHub Pull Request and decide which clusters and/or hubs  │
│                    require helm upgrades to be performed for their *hub helm charts or the support helm chart.       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `generate helm-upgrade-jobs`

This function consumes a list of files that have been added or modified, and from that deduces which hubs on which clusters require a helm upgrade, and whether the support chart also needs upgrading.
It constructs a human-readable table of the hubs that will be upgraded as a result of the changed files.

This function is primarily used in our CI/CD infrastructure and, on top of the human-readable output, JSON objects are also set as outputs that can be interpreted by GitHub Actions as matrix jobs.
This allows us to optimise and parallelise the automatic deployment of our hubs.

**Command line usage:**

```bash
                                                                                                                        
 Usage: deployer generate helm-upgrade-jobs [OPTIONS] CHANGED_FILEPATHS                                                 
                                                                                                                        
 Analyze added or modified files from a GitHub Pull Request and decide which clusters and/or hubs require helm upgrades 
 to be performed for their *hub helm charts or the support helm chart.                                                  
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    changed_filepaths      TEXT  Comma delimited list of files that have changed [default: None] [required]         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


#### `generate dedicated-cluster`
This generate sub-command can be used to create the initial files needed for a new cluster on GCP or AWS.

**Command line usage:**
```bash
                                                                                                                        
 Usage: deployer generate dedicated-cluster [OPTIONS] COMMAND [ARGS]...                                                 
                                                                                                                        
 Generate the initial files needed for a new cluster on GCP or AWS.                                                     
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ aws    Automatically generate the files required to setup a new cluster on AWS                                       │
│ gcp    Automatically generates the initial files, required to setup a new cluster on GCP                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

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
  - (`eksctl/template.json`)[https://github.com/2i2c-org/infrastructure/blob/master/eksctl/template.jsonnet]
  - (`terraform/aws/projects/basehub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/master/terraform/aws/projects/basehub-template.tfvars]

**Command line usage:**

```bash
 Usage: deployer generate dedicated-cluster aws [OPTIONS]                                                               
                                                                                                                        
 Automatically generate the files required to setup a new cluster on AWS                                                
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --cluster-name          TEXT  [default: None] [required]                                                          │
│ *  --hub-type              TEXT  [default: None] [required]                                                          │
│ *  --cluster-region        TEXT  [default: None] [required]                                                          │
│    --help                        Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

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
    - `hub_type` (basehub/daskhub) - whether the hub deployed there would need dask or not
    - `hub_name` - the name of the first hub which will be deployed in the cluster (usually `staging`)

The templates have a set of default features and define some opinionated characteristics for the cluster.
These defaults are described in each file template.

  The infrastructure terraform config is generated based on the terraform templates in:
    - (`terraform/basehub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/master/terraform/gcp/projects/basehub-template.tfvars]
    - (`terraform/daskhub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/master/terraform/gcp/projects/daskhub-template.tfvars]
  The cluster configuration directory is generated based on the templates in:
    - (`config/clusters/templates/gcp`)[https://github.com/2i2c-org/infrastructure/blob/master/config/clusters/templates/gcp]

**Command line usage:**

```bash
 Usage: deployer generate dedicated-cluster gcp [OPTIONS]                                                               
                                                                                                                        
 Automatically generates the initial files, required to setup a new cluster on GCP                                      
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --cluster-name          TEXT  [default: None] [required]                                                          │
│ *  --project-id            TEXT  [default: None] [required]                                                          │
│ *  --hub-name              TEXT  [default: None] [required]                                                          │
│    --cluster-region        TEXT  [default: us-central1]                                                              │
│    --hub-type              TEXT  [default: basehub]                                                                  │
│    --help                        Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


### The `grafana` sub-command
This deployer sub-command manages all of the available functions related to Grafana.

**Command line usage:**
```bash
                                                                                                                        
 Manages Grafana related workflows.                                                                                     
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ deploy-dashboards           Deploy the latest official JupyterHub dashboards to a cluster's grafana instance. This   │
│                             is done via Grafana's REST API, authorized by using a previously generated Grafana       │
│                             service account's access token.                                                          │
│ new-token                   Generate an API token for the cluster's Grafana `deployer` service account and store it  │
│                             encrypted inside a `enc-grafana-token.secret.yaml` file.                                 │
│ update-central-datasources  Update the central grafana with datasources for all clusters prometheus instances        │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `grafana deploy-dashboards`

This function uses [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) to create a set of grafana dashboards for monitoring hub usage across all hubs on a cluster.
The support chart **must** be deployed before trying to install the dashboards, since the support chart installs prometheus and grafana.

**Command line usage:**

```bash
                                                                                                                        
 Usage: deployer grafana deploy-dashboards [OPTIONS] CLUSTER_NAME                                                       
                                                                                                                        
 Deploy the latest official JupyterHub dashboards to a cluster's grafana instance. This is done via Grafana's REST API, 
 authorized by using a previously generated Grafana service account's access token.                                     
 The official JupyterHub dashboards are maintained in https://github.com/jupyterhub/grafana-dashboards along with a     
 python script to deploy them to Grafana via a REST API.                                                                
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
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

**Command line usage:**
```bash
                                                                                                                        
 Usage: deployer grafana new-token [OPTIONS] CLUSTER                                                                    
                                                                                                                        
 Generate an API token for the cluster's Grafana `deployer` service account and store it encrypted inside a             
 `enc-grafana-token.secret.yaml` file.                                                                                  
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster      TEXT  Name of cluster for who's Grafana deployment to generate a new deployer token                │
│                         [default: None]                                                                              │
│                         [required]                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
#### `grafana update-central-datasources`

Ensures that the central grafana at https://grafana.pilot.2i2c.cloud is
configured to use as datasource the authenticated prometheus instances of all
the clusters that we run.

**Command line usage:**
```bash
                                                                                                                        
 Usage: deployer grafana update-central-datasources [OPTIONS]                                                           
                                                                                                                        
 Update the central grafana with datasources for all clusters prometheus instances                                      
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --central-grafana-cluster        TEXT  Name of cluster where the central grafana lives [default: 2i2c]               │
│ --help                                 Show this message and exit.                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```


### The `validate` sub-command

This function is used to validate the values files for each of our hubs against their helm chart's values schema.
This allows us to validate that all required values are present and have the correct type before we attempt a deployment.

**Command line usage:**

```bash
 Validate configuration files such as helm chart values and cluster.yaml files.                                         
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ all                   Validate cluster.yaml and non-encrypted helm config for given hub                              │
│ authenticator-config  For each hub of a specific cluster: - It asserts that when the JupyterHub GitHubOAuthenticator │
│                       is used,   then `Authenticator.allowed_users` is not set.   An error is raised otherwise.      │
│ cluster-config        Validates cluster.yaml configuration against a JSONSchema.                                     │
│ hub-config            Validates the provided non-encrypted helm chart values files for each hub of a specific        │
│                       cluster.                                                                                       │
│ support-config        Validates the provided non-encrypted helm chart values files for the support chart of a        │
│                       specific cluster.                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### The `cilogon-client` sub-command for CILogon OAuth client management
Deployer sub-command for managing CILogon clients for 2i2c hubs.

**Command line usage:**
```bash
 Usage: deployer cilogon-client [OPTIONS] COMMAND [ARGS]...                                                                                                                        
                                                                                                                                                                                   
 Manage cilogon clients for hubs' authentication.                                                                                                                                  
                                                                                                                                                                                   
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ create     Create a CILogon client for a hub.                                                                                                                                   │
│ delete     Delete an existing CILogon client. This deletes both the CILogon client application, and the client credentials from the configuration file.                         │
│ get        Retrieve details about an existing CILogon client.                                                                                                                   │
│ get-all    Retrieve details about all existing 2i2c CILogon clients.                                                                                                            │
│ update     Update the CILogon client of a hub.                                                                                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `cilogon-client create/delete/get/get-all/update`

create/delete/get/get-all/update/ CILogon clients using the 2i2c administrative client provided by CILogon.

**Command line usage:**

- `cilogon-client create`

  ```bash
  Usage: deployer cilogon-client create [OPTIONS] CLUSTER_NAME HUB_NAME                                                  
                                        [HUB_TYPE] HUB_DOMAIN                                                            
                                                                                                                          
  Create a CILogon client for a hub.                                                                                     
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT        Name of cluster to operate on [default: None] [required]                          │
  │ *    hub_name          TEXT        Name of the hub for which we'll create a CILogon client [default: None]           │
  │                                    [required]                                                                        │
  │      hub_type          [HUB_TYPE]  Type of hub for which we'll create a CILogon client (ex: basehub, daskhub)        │
  │                                    [default: basehub]                                                                │
  │ *    hub_domain        TEXT        The hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud)           │
  │                                    [default: None]                                                                   │
  │                                    [required]                                                                        │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client delete`

  ```bash
  Usage: deployer cilogon-client delete [OPTIONS] CLUSTER_NAME HUB_NAME                                                  
                                                                                                                          
  Delete an existing CILogon client. This deletes both the CILogon client application, and the client credentials from   
  the configuration file.                                                                                                
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT  Name of cluster to operate [default: None] [required]                                   │
  │ *    hub_name          TEXT  Name of the hub for which we'll delete the CILogon client details [default: None]       │
  │                              [required]                                                                              │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --client-id        TEXT  (Optional) Id of the CILogon client to delete of the form `cilogon:/client_id/<id>`. If the │
  │                          id is not passed, it will be retrieved from the configuration file                          │
  │ --help                   Show this message and exit.                                                                 │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client get`

  ```bash
  Usage: Usage: deployer cilogon-client get [OPTIONS] CLUSTER_NAME HUB_NAME                                                     
                                                                                                                        
  Retrieve details about an existing CILogon client.                                                                     
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
  │ *    hub_name          TEXT  Name of the hub for which we'll retrieve the CILogon client details [default: None]     │
  │                              [required]                                                                              │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client-get-all`

  ```bash
  Usage: deployer cilogon-client get-all [OPTIONS]                                                                       
                                                                                                                          
  Retrieve details about all existing 2i2c CILogon OAuth clients.                                                        
                                                                                                                          
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client update`
  ```bash
  Usage: deployer cilogon-client update [OPTIONS] CLUSTER_NAME HUB_NAME                                                  
                                        HUB_DOMAIN                                                                       
                                                                                                                          
  Update the CILogon client of a hub.                                                                                    
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
  │ *    hub_name          TEXT  Name of the hub for which we'll update a CILogon client [default: None] [required]      │
  │ *    hub_domain        TEXT  The hub domain, as specified in `cluster.yaml` (ex: staging.2i2c.cloud) [default: None] │
  │                              [required]                                                                              │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

### The `exec` sub-command for executing shells and debugging commands

This deployer `exec` sub-command can be used to
exec a shell in various parts of the infrastructure.
It can be used for poking around, or debugging issues.

These are primarily helpful for manual actions when debugging issues (during
setup or an outage), or when taking down a hub. 

All these commands take a cluster and hub name as parameters, and perform appropriate
authentication before performing their function.

**Command line usage:**

```bash
 Usage: deployer exec [OPTIONS] COMMAND [ARGS]...                                                                       
                                                                                                                        
 Execute a shell in various parts of the infra. It can be used for poking around, or debugging issues.                  
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ debug                                                                                                                │
│ shell                                                                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
#### `exec debug`

This sub-command is useful for debugging.
**Command line usage:**

```bash
 Usage: deployer exec debug [OPTIONS] COMMAND [ARGS]...                                                                 
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ component-logs              Display logs from a particular component on a hub on a cluster                           │
│ start-docker-proxy          Proxy a docker daemon from a remote cluster to local port 23760.                         │
│ user-logs                   Display logs from the notebook pod of a given user                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `exec debug component-logs`

This subcommand displays live updating logs of a particular core component of a particular
JupyterHub on a given cluster. You can pass `--no-follow` to provide just
logs upto the current point in time and then stop. If the component pod has restarted
due to an error, you can pass `--previous` to look at the logs of the pod
prior to the last restart.

```bash
  Usage: deployer exec debug component-logs [OPTIONS] CLUSTER_NAME HUB_NAME                                              
                                           COMPONENT:{hub|proxy|dask-gateway-                                           
                                           api|dask-gateway-controller|dask-                                            
                                           gateway-traefik}                                                             
                                                                                                                        
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

##### `exec debug user-logs`

This subcommand displays live updating logs of a prticular user on a hub if
it is currently running. If sidecar containers are present (such as per-user db),
they are ignored and only the notebook logs are provided. You can pass
`--no-follow` to provide logs upto the current point only.

```bash
 Usage: deployer exec debug user-logs [OPTIONS] CLUSTER_NAME HUB_NAME USERNAME                                          
                                                                                                                        
 Display logs from the notebook pod of a given user                                                                     
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
│ *    username          TEXT  Name of the JupyterHub user to get logs for [default: None] [required]                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --follow      --no-follow        Live update new logs as they show up [default: follow]                              │
│ --previous    --no-previous      If user pod has restarted, show logs from just before the restart                   │
│                                  [default: no-previous]                                                              │
│ --help                           Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `exec debug start-docker-proxy`

Building docker images locally can be *extremely* slow and frustrating. We run a central docker daemon
in our 2i2c cluster that can be accessed via this command, and speeds up image builds quite a bit!
Once you run this command, run `export DOCKER_HOST=tcp://localhost:23760` in another terminal to use the faster remote
docker daemon.

```bash
 Usage: deployer exec debug start-docker-proxy [OPTIONS]                                                                
                                               [DOCKER_DAEMON_CLUSTER]                                                  
                                                                                                                        
 Proxy a docker daemon from a remote cluster to local port 23760.                                                       
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   docker_daemon_cluster      [DOCKER_DAEMON_CLUSTER]  Name of cluster where the docker daemon lives [default: 2i2c]  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### `exec shell`
This exec sub-command can be used to aquire a shell in various places of the infrastructure.

```bash
Usage: deployer exec shell [OPTIONS] COMMAND [ARGS]...                                                                 
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ aws      Exec into a shall with appropriate AWS credentials (including MFA)                                          │
│ homes    Pop an interactive shell with the home directories of the given hub mounted on /home                        │
│ hub      Pop an interactive shell in the hub pod                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `exec shell hub`

This subcommand gives you an interactive shell on the hub pod itself, so you
can poke around to see what's going on. Particularly useful if you want to peek
at the hub db with the `sqlite` command.

```bash
  Usage: deployer exec shell hub [OPTIONS] CLUSTER_NAME HUB_NAME                                                         
                                                                                                                        
 Pop an interactive shell in the hub pod                                                                                
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `exec shell homes`

This subcommand gives you a shell with the home directories of all the
users on the given hub in the given cluster mounted under `/home`.
Very helpful when doing (rare) manual operations on user home directories,
such as renames.

When you exit the shell, the temporary pod spun up is removed.

```bash
 Usage: deployer exec shell homes [OPTIONS] CLUSTER_NAME HUB_NAME                                                       
                                                                                                                        
 Pop an interactive shell with the home directories of the given hub mounted on /home                                   
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
│ *    hub_name          TEXT  Name of hub to operate on [default: None] [required]                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

##### `exec shell aws`

This sub-command can exec into a shall with appropriate AWS credentials (including MFA).

```bash
 Usage: deployer exec shell aws [OPTIONS] PROFILE MFA_DEVICE_ID AUTH_TOKEN                                              
                                                                                                                        
 Exec into a shall with appropriate AWS credentials (including MFA)                                                     
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    profile            TEXT     Name of AWS profile to operate on [default: None] [required]                        │
│ *    mfa_device_id      TEXT     Full ARN of MFA Device the code is from [default: None] [required]                  │
│ *    auth_token         INTEGER  6 digit 2 factor authentication code from the MFA device [default: None] [required] │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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
