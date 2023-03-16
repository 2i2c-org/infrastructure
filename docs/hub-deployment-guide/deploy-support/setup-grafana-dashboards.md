(setup-grafana)=
# Setup grafana dashboards

Now, we will deploy some specific dashboards to the grafana instance we deployed as part of [](deploy-support-chart).

````{seealso}
It is also possible to [enable logging in with GitHub](grafana-dashboards:github-auth)
to allow Community Representatives and Hub Administrators to access these dashboards as well.
```{warning}
We should enable GitHub login for _all_ Grafana dashboards running on **dedicated**
clusters, so the Community Representatives have access to them.
```
````

(setup-grafana:log-in)=
## Login to the cluster-specific grafana

Eventually, visiting `GRAFANA_URL` (which we set in [](deploy-support-chart)) will present you with a login page.
Here are the credentials for logging in:

- **username**: `admin`
- **password**: located in `helm-charts/support/enc-support.secret.values.yaml` (`sops` encrypted).

## Create an API key to auto-deploy the dashboards

Once the support chart is deployed and you are able to log into grafana as the
admin user, you can generate an API key.

You can do this by running a deployer command:

```bash
export CLUSTER_NAME=<cluster-name>
```

```bash
deployer new-grafana-token $CLUSTER_NAME
```

If the command succeeded, it should have created:

- a [Grafana service account](https://grafana.com/docs/grafana/latest/administration/service-accounts/) named `deployer`
- a token named `deployer` for this service account
- the following sops-ecrypted file `config/clusters/<cluster>/enc-grafana-token.secret.yaml`,
  with a content similar to:

  ```yaml
  grafana_token: token
  ```

The encrypted file can now be committed to the repository.

```{note}
This key will be used by the [`deploy-grafana-dashboards` workflow](https://github.com/2i2c-org/infrastructure/tree/HEAD/.github/workflows/deploy-grafana-dashboards.yaml) to deploy some default grafana dashboards for JupyterHub using [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards).
```

## Deploying the Grafana Dashboards locally

You can deploy the dashboards locally using the deployer:

```bash
deployer deploy-grafana-dashboards $CLUSTER_NAME
```

## Deploying the Grafana Dashboards from CI/CD

Once you've pushed the encrypted `grafana_token` to the GitHub repository, it will be possible to manually trigger the `deploy-grafana-dashboards` workflow using the ["Run workflow" button](https://github.com/2i2c-org/infrastructure/actions/workflows/deploy-grafana-dashboards.yaml) to deploy the dashboards.

You will first need to add the name of the cluster as a matrix entry in the [`deploy-grafana-dashboards.yaml` workflow file](https://github.com/2i2c-org/infrastructure/blob/008ae2c1deb3f5b97d0c334ed124fa090df1f0c6/.github/workflows/deploy-grafana-dashboards.yaml#L12) and commit the change to the repo.

```{note}
The workflow only runs when manually triggered.

Any re-triggering of the workflow after the initial deployment will overwrite any dashboard created from the Grafana UI and not stored in the [`jupyterhub/grafana-dashboards`](https://github.com/jupyterhub/grafana-dashboards) repository.
```
