(topic:billing:cost-attribution)=
# Cost Attribution System

The Cost Attribution System is designed to monitor and attribute cloud
infrastructure costs to specific hub deployments managed. This system
integrates with the [AWS Cost Explorer
API](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html)
to provide detailed cost insights within a hub's Grafana dashboard.

{{% callout note %}} Note that this feature is currently available to AWS
hosted hubs only and will be rolled out to other cloud providers in the
future. {{% /callout %}}

## Components

1. AWS IAM Role Configuration

A [dedicated IAM
role](https://github.com/2i2c-org/infrastructure/blob/main/terraform/aws/aws-ce-grafana-backend-iam.tf)
is created to grant the necessary permissions for accessing the Cost Explorer
API.

2. Python Web Server

A [Python-based web
server](https://github.com/2i2c-org/infrastructure/tree/main/helm-charts/images/aws-ce-grafana-backend)
is deployed to interact with the Cost Explorer API. It retrieves cost data
and serves it as JSON, making it accessible for Grafana.

3. Grafana Integration

A custom Helm chart,
[`aws-ce-grafana-backend`](https://github.com/2i2c-org/infrastructure/tree/main/helm-charts/aws-ce-grafana-backend),
is introduced to facilitate the deployment of the Python web server alongside
Grafana.

This enables Grafana to query the web server for cost data, allowing users to
visualize and analyze cloud expenses directly within the Grafana interface.

It
[uses](https://github.com/2i2c-org/infrastructure/blob/48e06a02a411e31b03db2f30fd6a090b5f6eeeb5/helm-charts/support/values.yaml#L405-L406)
the [Infinity Grafana
plugin](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/)
to serve JSON from AWS Cost Explorer API, for use by Grafana dashboard
panels.

## Technical implementation details

The system relies on _at least one of these tags_ to be on any cloud infra to
attribute cost to.

- `2i2c.org/cluster-name`
- `alpha.eksctl.io/cluster-name`
- `kubernetes.io/cluster/<cluster name>`

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
cost attribution though.
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

```{important}
There are still some clusters that don't have separate EFS storage per hub yet.
```
