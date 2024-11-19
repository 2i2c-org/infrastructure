# About these grafana dashboard files

These are dashboard definitions as jsonnet templates. They are deployed using a
Python script from https://github.com/jupyterhub/grafana-dashboards, which can be
done via the deployer command:

```bash
deployer grafana deploy-dashboards $CLUSTER_NAME
```

Running this command has a pre-requisite that you have jsonnet installed,
specifically the jsonnet binary built using golang called go-jsonnet.

To just render the jsonnet templates, which is relevant during development, you
can:

1. Clone https://github.com/jupyterhub/grafana-dashboards somewhere
2. Go to that folder, and then run something like:
   ```bash
   jsonnet -J vendor /some/path/2i2c-org/infrastructure/grafana-dashboards/cloud-cost-aws.jsonnet
   ```
