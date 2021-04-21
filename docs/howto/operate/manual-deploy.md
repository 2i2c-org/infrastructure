# Manually deploy a hub

The [`deploy.py`](https://github.com/2i2c-org/pilot-hubs/blob/master/deploy.py) script is a cmd utility built to help deploy one or all the hubs to their Kubernetes clusters, but  also to build the user image. Checkout the [](../configure/update-env.md) section on how to use the deploy script to update the user environment.

## Deploy script arguments and usage
Running:
```
python3 deploy.py deploy --help
```
Will provide information about the `deploy.py` deploy options:

```bash
usage: deploy.py deploy [-h] [--skip-hub-health-test]
                        [cluster_name] [hub_name]

positional arguments:
  cluster_name
  hub_name

optional arguments:
  -h, --help            show this help message and exit
  --skip-hub-health-test

```

* `cluster_name` argument

    Deploys all the hubs in the cluster passed as argument. Cluster config is read
    from `config/hubs/{cluster_name}.cluster.yaml`
    ```bash
    python3 deploy.py deploy <cluster>
    ```
* `hub_name` argument

    Deploys only the hub passed as argument. 

    ```bash
    python3 deploy.py deploy <cluster> <hub>
    ```
* `--skip-hub-health-test` flag

    Skips the default health checks ran by the deploy script. Checkout [testing the hub section](test-hub.md) to learn more about the hub health tests.
    ```bash
    python3 deploy.py deploy --skip-hub-health-test
    ```

### Authentication

Secret keys required to deploy hubs are located in `config/secrets.yaml`, and encrypted
via [`sops`](https://github.com/mozilla/sops/). You must have acces to the `two-eye-two-see`
GCP project, and [set up sops](https://github.com/mozilla/sops#23encrypting-using-gcp-kms)
to be usable with it before you can do deployments.