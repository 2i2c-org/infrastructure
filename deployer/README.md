# The `deployer` module

## Installing dependencies

```bash
pip install -r requirements.txt
```

## Functions

```bash
usage: python deployer [-h]
                {deploy,validate,deploy-support,deploy-grafana-dashboards,use-cluster-credentials,generate-helm-upgrade-jobs,run-hub-health-check}
                ...

A command line tool to perform various functions related to deploying and maintaining a JupyterHub running on kubernetes infrastructure

positional arguments:
  {deploy,validate,deploy-support,deploy-grafana-dashboards,use-cluster-credentials,generate-helm-upgrade-jobs,run-hub-health-check}
                        Available subcommands
    deploy              Install/upgrade the helm charts of JupyterHubs on a cluster
    validate            Validate the cluster.yaml configuration itself, as well as the provided non-encrypted helm chart values files for each
                        hub or the specified hub.
    deploy-support      Install/upgrade the support helm release on a given cluster
    deploy-grafana-dashboards
                        Deploy grafana dashboards to a cluster for monitoring JupyterHubs. deploy-support must be run first!
    use-cluster-credentials
                        Modify the current kubeconfig with the deployer's access credentials for the named cluster
    generate-helm-upgrade-jobs
                        Generate a set of matrix jobs to perform a helm upgrade in parallel across clusters and hubs. Emit JSON to stdout that
                        can be read by the strategy.matrix field of a GitHub Actions workflow.
    run-hub-health-check
                        Run a health check against a given hub deployed on a given cluster

optional arguments:
  -h, --help            show this help message and exit
```

### `deploy`

```bash
usage: python deployer deploy [-h] [--skip-hub-health-test] [--config-path CONFIG_PATH] cluster_name [hub_name]

positional arguments:
  cluster_name          The name of the cluster to perform actions on
  hub_name              The hub, or list of hubs, to install/upgrade the helm chart for

optional arguments:
  -h, --help            show this help message and exit
  --skip-hub-health-test
                        Bypass the hub health test
  --config-path CONFIG_PATH
                        File to read secret deployment configuration from
```

### `validate`

```bash
usage: python deployer validate [-h] cluster_name [hub_name]

positional arguments:
  cluster_name  The name of the cluster to perform actions on
  hub_name      The hub, or list of hubs, to validate provided non-encrypted helm chart values for.

optional arguments:
  -h, --help    show this help message and exit
```

### `deploy-support`

```bash
usage: python deployer deploy-support [-h] cluster_name

positional arguments:
  cluster_name  The name of the cluster to perform actions on

optional arguments:
  -h, --help    show this help message and exit
```

### `deploy-grafana-dashboards`

```bash
usage: python deployer deploy-grafana-dashboards [-h] cluster_name

positional arguments:
  cluster_name  The name of the cluster to perform actions on

optional arguments:
  -h, --help    show this help message and exit
```

### `use-cluster-credentials`

```bash
usage: python deployer use-cluster-credentials [-h] cluster_name

positional arguments:
  cluster_name  The name of the cluster to perform actions on

optional arguments:
  -h, --help    show this help message and exit
```

### `generate-helm-upgrade-jobs`

```bash
usage: python deployer generate-helm-upgrade-jobs [-h] [filepaths]

positional arguments:
  filepaths   A singular or space-delimited list of added or modified filepaths in the repo

optional arguments:
  -h, --help  show this help message and exit
```

### `run-hub-health-check`

```bash
usage: python deployer run-hub-health-check [-h] [--check-dask-scaling] cluster_name hub_name

positional arguments:
  cluster_name          The name of the cluster to perform actions on
  hub_name              The hub to run health checks against.

optional arguments:
  -h, --help            show this help message and exit
  --check-dask-scaling  For daskhubs, optionally check that dask workers can be scaled
```

### Running Tests

```bash
pip install -r dev-requirements.txt
python -m pytest -vvv
```
