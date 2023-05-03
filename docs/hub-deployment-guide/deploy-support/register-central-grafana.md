# Register the cluster's Prometheus server with the central Grafana

Once you have [deployed the support chart](deploy-support-chart), you must also register this cluster as a datasource for the [central Grafana dashboard](grafana-dashboards:central). This will allow you to visualize cluster statistics not only from the cluster-specific Grafana deployement but also from the central dashboard, that aggregates data from all the clusters.

## Create a `support.secret.values.yaml` file

Only 2i2c staff and our centralized grafana should be able to access the prometheus data on a cluster from outside the cluster.
The [basic auth](https://kubernetes.github.io/ingress-nginx/examples/auth/basic/) feature of nginx-ingress is used to restrict this.
A `support.secret.values.yaml` file is used to provide these secret credentials, which we create under the relevant `config/clusters/<cluster-name>/` folder.
It requires the following configuration:

```yaml
prometheusIngressAuthSecret:
  username: <output of pwgen -s 64 1>
  password: <output of pwgen -s 64 1>
```

```{note}
We use the [pwgen](https://linux.die.net/man/1/pwgen) program, commonly
installed by default in many operating systems, to generate the password.
```

Once you create the file, encrypt it with `sops`.

```bash
export CLUSTER_NAME=<cluster-name>
```

```bash
sops --output config/clusters/$CLUSTER_NAME/enc-support.secret.values.yaml --encrypt config/clusters/$CLUSTER_NAME/support.secret.values.yaml
```

## Update your `cluster.yaml` file

Update the `support` config in the cluster's `cluster.yaml` file to include the encrypted secret file.

```yaml
support:
  helm_chart_values_files:
    - support.values.yaml
    - enc-support.secret.values.yaml
```

Then redeploy the `support chart`.

```bash
deployer deploy-support $CLUSTER_NAME
```

## Link the cluster's Prometheus server to the central Grafana

Run `deployer update-central-grafana-datasources` to register the new prometheus with the default central grafana.
