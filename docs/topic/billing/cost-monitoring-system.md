(topic:billing:cost-monitoring)=
# Cost Monitoring System

The Cost Monitoring System is designed to monitor and attribute cloud
infrastructure costs to 2i2c hub deployments. This system integrates with the
[AWS Cost Explorer
API](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html)
to provide detailed cost insights from a hub's Grafana dashboard.

:::{note}
This feature is currently available to AWS
hosted hubs only and will be rolled out to other cloud providers in the
future.
:::

## Components

### 1. AWS IAM Role Configuration

  A [dedicated IAM
  role](https://github.com/2i2c-org/infrastructure/blob/main/terraform/aws/cost-monitoring.tf)
  called `jupyterhub_cost_monitoring_iam_role` is created using terraform in order to grant the necessary permissions for accessing the Cost Explorer
  API.

### 2. JupyterHub Cost Monitoring

  A [Python-based web
  server](https://github.com/2i2c-org/jupyterhub-cost-monitoring/)
  is deployed to interact with the Cost Explorer API. It retrieves cost data
  from the AWS Cost Explorer API and serves it as JSON for Grafana to consume.

  The helm deployment is unconditionally enabled, unless explicitly overridden in the `config/clusters/<cluster_name>/support.values.yaml` file, and the configuration is automatically defined in the `helm-charts/support/values.jsonnet` file.

### 3.  Grafana Dashboard

  A [custom dashboard](https://github.com/2i2c-org/infrastructure/tree/main/grafana-dashboards) is presently defined in the infrastructure repository (to be upstreamed to [jupyterhub/grafana-dashboards](https://github.com/jupyterhub/grafana-dashboards)).

  This enables Grafana to query the web server for cost data, allowing users to
  visualize and analyze cloud expenses directly within the Grafana interface.

  It
  [uses](https://github.com/2i2c-org/infrastructure/blob/48e06a02a411e31b03db2f30fd6a090b5f6eeeb5/helm-charts/support/values.yaml#L405-L406)
  the [Infinity Grafana
  plugin](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/)
  to serve JSON from AWS Cost Explorer API, for use by Grafana dashboard
  panels.

## Technical implementation

The system relies on _at least one of these tags_ activated to track resource cost allocations:

- `2i2c:hub-name`
- `2i2c:node-purpose`
- `2i2c.org/cluster-name`
- `alpha.eksctl.io/cluster-name`
- `kubernetes.io/cluster/<cluster_name>`
- `kubernetes.io/created-for/pvc/name`
- `kubernetes.io/created-for/pvc/namespace`

```{important}
Currently, on clusters that have a k8s version greater or equal with 1.30,
terraform managed resources already have the `2i2c.org/cluster-name`
tag configured via the `default_tags` variable, and eksctl managed resources
already have the tag configured for node groups via `nodegroup.libsonnet`.

On clusters that have a k8s version less than 1.30, eksctl managed resources,
the `alpha.eksctl.io/cluster-name` and `kubernetes.io/cluster/<cluster name>`
tags are present and used instead.

New clusters have _all_ eksctl managed resources configured to be tagged, not
just the node groups. This isn't important to ensure for existing clusters'
cost monitoring though.
```

The system also relies on the tag `2i2c:hub-name` to be specified in addition to
the tags above for any cloud infra tied to specific hubs.

We only need to ensure the `2i2c.org/cluster-name` and `2i2c:hub-name` tags are
declared, the others are applied by `eksctl` and Kubernetes controllers that can
create cloud resources to represent k8s resources (block storage volumes for k8s
PV resources referencing certain storage classes, and load balancers for k8s
Service's of type LoadBalancer).

The following resources are known to be hub specific in some cases and known
to incur costs.

- **S3 buckets** in terraform
- **EFS storage** in terraform
- **EBS volumes** in terraform
- **Node groups** in eksctl
