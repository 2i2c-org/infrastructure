(hub-deployment-guide:runbooks:phase2)=
# Phase 2: Cluster setup

This assumes all engineers have access to this new account, and will be able to set up the cluster and support, without any new hubs being set up.

## Definition of ready

The following lists the information that needs to be available to the engineer before this phase can start.

- Region / Zone of the cluster
- Name of cluster
- Is GPU required?

## Outputs

At the end of Phase 2, there should be a new cluster setup, with fully configured and deployed support components.

The file assets that should have been included in the PR should be:

```bash
➕ config/clusters/<new-cluster-name>
  ├── cluster.yaml
  ├── enc-deployer-credentials.secret.json
  ├── enc-support.secret.values.yaml
  ├── enc-grafana-token.secret.yaml
  └── support.values.yaml
```

```bash
➕ terraform/<cloud-provider>/projects
  └── <new-cluster>.tfvars
```

If on AWS:

```bash
➕ eksctl
  ├── <new-cluster>.jsonnet
  ├── ssh-keys/
    ├── <new-cluster>.key.pub
    ├── secret
    └   └── <new-cluster>.key
```

And the following existing file should be updated to accommodate the new cluster:

```bash
～ .github/workflows
  └── deploy-grafana-dashboards.yaml
```

```{tip}
When reviewing cluster setup PRs, make sure the files above are all present.
```

## Cluster setup runbook

All of the following steps must be followed in order to consider phase 2 complete. Steps contain references to other smaller, topic-specifc runbooks that are gathered together and listed in the order they should be carried on by an engineer.

1. **Create the new cluster**

   Follow the provider-specific steps in [](new-cluster:new-cluster) to create the cluster.

2. **Configure and deploy the support chart**

   Follow the steps in [](deploy-support-chart) to configure and deploy the support chart.

3. **Setup Grafana dashboards**

   Follow the steps in [](setup-grafana) to setup Grafana dashboards for the newly created cluster.

4. **Register the new cluster with the central 2i2c Grafana**

   Follow the steps in [](register-new-cluster-with-central-grafana) so that the cluster you just added will be findable from the 2i2c central Grafana.
