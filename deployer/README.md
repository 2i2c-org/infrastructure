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

``` bash
                                                                                                                                              
 Usage: deployer [OPTIONS] COMMAND [ARGS]...                                                                            
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                              │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.       │
│ --help                        Show this message and exit.                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ cilogon-client-create               Create a CILogon OAuth client for a hub.                                         │
│ cilogon-client-delete               Delete an existing CILogon client.                                               │
│ cilogon-client-get                  Retrieve details about an existing CILogon client.                               │
│ cilogon-client-get-all              Retrieve details about all existing 2i2c CILogon OAuth clients.                  │
│ cilogon-client-update               Update the CILogon OAuth client of a hub.                                        │
│ component-logs                      Display logs from a particular component on a hub on a cluster                   │
│ decrypt-age                         Decrypt secrets sent to `support@2i2c.org` via `age`                             │
│ deploy                              Deploy one or more hubs in a given cluster                                       │
│ deploy-grafana-dashboards           Deploy JupyterHub dashboards to grafana set up in the given cluster              │
│ deploy-support                      Deploy support components to a cluster                                           │
│ exec-homes-shell                    Pop an interactive shell with the home directories of the given hub mounted on   │
│                                     /home                                                                            │
│ exec-hub-shell                      Pop an interactive shell in the hub pod                                          │
│ generate-aws-cluster                Automatically generate the files required to setup a new cluster on AWS          │
│ generate-gcp-cluster                Automatically generates the initial files, required to setup a new cluster on    │
│                                     GCP                                                                              │
│ generate-helm-upgrade-jobs          Analyse added or modified files from a GitHub Pull Request and decide which      │
│                                     clusters and/or hubs require helm upgrades to be performed for their *hub helm   │
│                                     charts or the support helm chart.                                                │
│ new-grafana-token                   Generate an API token for the cluster's Grafana `deployer` service account and   │
│                                     store it encrypted inside a `enc-grafana-token.secret.yaml` file.                │
│ run-hub-health-check                Run a health check on a given hub on a given cluster. Optionally check scaling   │
│                                     of dask workers if the hub is a daskhub.                                         │
│ start-docker-proxy                  Proxy a docker daemon from a remote cluster to local port 23760.                 │
│ update-central-grafana-datasources  Update the central grafana with datasources for all clusters prometheus          │
│                                     instances                                                                        │
│ use-cluster-credentials             Pop a new shell authenticated to the given cluster using the deployer's          │
│                                     credentials                                                                      │
│ user-logs                           Display logs from the notebook pod of a given user                               │
│ validate                            Validate cluster.yaml and non-encrypted helm config for given hub                │
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

### `new-grafana-token`
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

### `generate-aws-cluster`

This function generates the required files for an AWS cluster based on a few input fields,
the name of the cluster, the region where the cluster will be deployed and whether the hub deployed there would need dask or not.

  Generates:
  - an eksctl jsonnet file
  - a .tfvars file
  - An ssh-key (the private part is encrypted)

The files are generated based on the jsonnet templates in:
  - (`eksctl/template.json`)[https://github.com/2i2c-org/infrastructure/blob/master/eksctl/template.jsonnet]
  - (`terraform/aws/projects/basehub-template.tfvars`)[https://github.com/2i2c-org/infrastructure/blob/master/terraform/aws/projects/basehub-template.tfvars]

**Command line usage:**

```bash
 Usage: deployer generate-aws-cluster [OPTIONS]                                                                         
                                                                                                                        
 Automatically generate the files required to setup a new cluster on AWS                                                
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --cluster-name          TEXT  [default: None] [required]                                                          │
│ *  --hub-type              TEXT  [default: None] [required]                                                          │
│ *  --cluster-region        TEXT  [default: None] [required]                                                          │
│    --help                        Show this message and exit.                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### `generate-gcp-cluster`

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
 Usage: deployer generate-gcp-cluster [OPTIONS]                                                                         
                                                                                                                        
 Automatically generate the files required to setup a new cluster on GCP                                                
                                                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --cluster-name          TEXT  [default: None] [required]                                                          │
│ *  --hub-type              TEXT  [default: None] [required]                                                          │
│ *  --cluster-region        TEXT  [default: None] [required]                                                          │
│ *  --cluster-zone          TEXT  [default: None] [required]                                                          │
│    --help                        Show this message and exit.                                                         │
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

### `update-central-grafana-datasources`

Ensures that the central grafana at https://grafana.pilot.2i2c.cloud is
configured to use as datasource the authenticated prometheus instances of all
the clusters that we run.

**Command line usage:**
```
                                                                                                                        
 Usage: deployer update-central-grafana-datasources [OPTIONS]                                                           
                                                    [CENTRAL_GRAFANA_CLUSTER]                                           
                                                                                                                        
 Update a central grafana with datasources for all our prometheuses                                                     
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   central_grafana_cluster      [CENTRAL_GRAFANA_CLUSTER]  Name of cluster where the central grafana lives            │
│                                                           [default: 2i2c]                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## Support helper tools

### `decrypt-age`

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

## CILogon OAuth clients management tools

### `cilogon_client_create/delete/get/get-all/update`

create/delete/get/get-all/update/ CILogon clients using the 2i2c administrative client provided by CILogon.

**Command line usage:**

- `cilogon-client-create`

  ```bash
  Usage: deployer cilogon-client-create [OPTIONS] CLUSTER_NAME HUB_NAME                                                  
                                        [HUB_TYPE] CALLBACK_URL                                                          
                                                                                                                          
  Create a CILogon OAuth client for a hub.                                                                               
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT        Name of cluster to operate on [default: None] [required]                          │
  │ *    hub_name          TEXT        Name of the hub for which we'll create a CILogon client [default: None]           │
  │                                    [required]                                                                        │
  │      hub_type          [HUB_TYPE]  Type of hub for which we'll create a CILogon client (ex: basehub, daskhub)        │
  │                                    [default: basehub]                                                                │
  │ *    callback_url      TEXT        URL that is invoked after OAuth authorization [default: None] [required]          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client-delete`

  ```bash
  Usage: deployer cilogon-client-delete [OPTIONS] [CLUSTER_NAME] [HUB_NAME]                                              
                                                                                                                          
  Delete an existing CILogon client.                                                                                     
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │   cluster_name      [CLUSTER_NAME]  Name of cluster to operate or none if --client_id is passed                      │
  │   hub_name          [HUB_NAME]      Name of the hub for which we'll delete the CILogon client details or none if     │
  │                                     --client_id is passed                                                            │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --client-id        TEXT  Id of the CILogon OAuth client to delete of the form cilogon:/client_id/<id>                │
  │ --help                   Show this message and exit.                                                                 │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client-get`

  ```bash
  Usage: deployer cilogon-client-get [OPTIONS] CLUSTER_NAME HUB_NAME                                                     
                                                                                                                          
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
  Usage: deployer cilogon-client-get-all [OPTIONS]                                                                       
                                                                                                                          
  Retrieve details about all existing 2i2c CILogon OAuth clients.                                                        
                                                                                                                          
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ```

- `cilogon-client-update`
  ```bash
  Usage: deployer cilogon-client-update [OPTIONS] CLUSTER_NAME HUB_NAME                                                  
                                        CALLBACK_URL                                                                     
                                                                                                                          
  Update the CILogon OAuth client of a hub.                                                                              
                                                                                                                          
  ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ *    cluster_name      TEXT  Name of cluster to operate on [default: None] [required]                                │
  │ *    hub_name          TEXT  Name of the hub for which we'll update a CILogon client [default: None] [required]      │
  │ *    callback_url      TEXT  New callback_url to associate with the client. This URL is invoked after OAuth          │
  │                              authorization                                                                           │
  │                              [default: None]                                                                         │
  │                              [required]                                                                              │
  ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
  │ --help          Show this message and exit.                                                                          │
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
│ --follow      --no-follow        Live update new logs as they show up [default: follow]                              │
│ --previous    --no-previous      If user pod has restarted, show logs from just before the restart                   │
│                                  [default: no-previous]                                                              │
│ --help                           Show this message and exit.                                                         │
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


### `start-docker-proxy`

Building docker images locally can be *extremely* slow and frustrating. We run a central docker daemon
in our 2i2c cluster that can be accessed via this command, and speeds up image builds quite a bit!
Once you run this command, run `export DOCKER_HOST=tcp://localhost:23760` in another terminal to use the faster remote
docker daemon.

```
 Usage: deployer start-docker-proxy [OPTIONS] [DOCKER_DAEMON_CLUSTER]                                                   
                                                                                                                        
 Proxy a docker daemon from a remote cluster to local port 23760.                                                       
                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   docker_daemon_cluster      [DOCKER_DAEMON_CLUSTER]  Name of cluster where the docker daemon lives [default: 2i2c]  │
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
