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

* Running the script without arguments

    Deploys all cluster and hubs in the `hubs.yaml` file.
    ```bash
    python3 deploy.py deploy
    ```
* `cluster_name` argument

    Deploys all the hubs in the cluster passed as argument (the hubs listed in `hubs.yaml` file unde `<cluster>`)
    ```bash
    python3 deploy.py deploy <cluster>
    ```
* `hub_name` argument

    Deploys only the hub passed as argument. The cluster must match the hub's cluster listed in the `hubs.yaml`.
    ```bash
    python3 deploy.py deploy <cluster> <hub>
    ```
* `--skip-hub-health-test` flag

    Skips the default health checks ran by the deploy script. Checkout [testing the hub section](test-hub.md) to learn more about the hub health tests.
    ```bash
    python3 deploy.py deploy --skip-hub-health-test
    ```

### Pre-requisites

Before using any of these `deploy.py` commands, you first need to make sure you are authenticated in all the right places and have the right credentials exported as environmental variables. This is because the deploy script need to be able to authenticate into the given cluster and have access to the unique `proxy.secretToken` needed to deploy the proxy pod. It also needs to know how to connect to the Auth0 account in order to determine and configure each hub's auth provider.

```{note}
To enable the deploy script to authenticate into the cluster, you only need to be authenticated into the `two-eye-two-see` project. This is because there are [sops](https://github.com/mozilla/sops) encrypted credentials for everything needed under `secrets/` with the key being in the `two-eye-two-see` project. Checkout the [*Project Access*](cmd-access.md) section for more info.
```

#### PROXY_SECRET_KEY
The `proxy.secretToken` needs to be unique to each hub, so this is generated based on a combination of `PROXY_SECRET_KEY` and the name of each hub. For the `deploy.py` script to work, the `PROXY_SECRET_KEY` needs to be available to it as an environmental variable.

You can generate a `PROXY_SECRET_KEY` to test the *staging hub* deploy with:
```bash
openssl rand -hex 32
```

```{note}
However, note that each `PROXY_SECRET_KEY` change will generate a `proxy.secretToken` change and that causes a pod restart with downtime.
```
Right now, the "official" `PROXY_SECRET_KEY` is the one used by GitHub actions. However we don't have **yet** a secure sharing mechanism of this secret with all the hub admins.

#### Auth0 client id and secret
The Auth0 credentials needed by the `deploy.py` script need to be exported as `AUTH0_MANAGEMENT_CLIENT_ID` and `AUTH0_MANAGEMENT_CLIENT_SECRET`. The management API client id and secret can be found in “APIs” section of your 2i2c Auth0 account. Checkout this [step by step guide](https://community.auth0.com/t/client-id-and-secret-for-management-api/21306/2) on the Auth0 community forum to get more info.