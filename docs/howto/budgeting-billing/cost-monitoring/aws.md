(howto:cost-monitoring:enable-aws)=
# Enable JupyterHub Cost Monitoring

The JupyterHub Cost Monitoring system consists of the [jupyterhub-cost-monitoring](https://github.com/2i2c-org/jupyterhub-cost-monitoring/) backend and Grafana cloud cost dashboards
that use the backend as a data source.

Checkout the [topic guide](topic:billing:cost-monitoring) for more information on the system.

## Steps

### 1. Enable cost allocation tags

Enabling cost allocation tags via terraform can be done for AWS
accounts that we have billing permissions for, but not for standalone accounts that communities manage themselves.

If cost allocation tags are not activated, then you can set

```yaml
jupyterhub-cost-monitoring:
  enabled: false
```

in the `config/clusters/<cluster_name>/support.values.yaml` file to disable deployment of the cost monitoring system.

`````{tab-set}

````{tab-item} Member account (2i2c SSO)
:sync: member-2i2c

AWS accounts that can be accessed with the [2i2c SSO](cloud-access:aws-sso) have cost allocation tags already enabled.

See the [topic guide](topic:billing:cost-monitoring) for more information on which cost allocation tags are activated.
````

````{tab-item} Standalone account with billing permissions
:sync: standalone

The relevant tags are already present in the terraform template used to generate
the new cluster and will be applied when creating the cluster.

If the apply operation fails with the following errors:

1. _Tag keys not found_

   While it sounds like cloud resources haven't been tagged, its probably because
   the billing system hasn't yet detected them. It runs a few times a day, so you
   may need to wait a few hours for the billing system to have detected each tag
   at least once.

2. _Linked account doesn't have access to cost allocation tags._

   This means we do not have billing permissions on the AWS account and is likely managed by a community (see Community-managed account).
````

````{tab-item} Community-managed account without billing permissions
:sync: member-community

We require a community member with the relevant billing permissions to enable the cost allocation tags on our behalf.

Below is a template message you can send to the technical contact. Note that `<cluster_name>` should be updated to the community's cluster name.

```
In order for 2i2c to enable the cloud cost monitoring feature for your community, the following changes needs to be made in the AWS organization's management account:

1. Declare that linked member accounts are allowed to access Cost Explorer.

   This can be done via "Billing and Cost Management" -> "Cost Management Preferences", where the checkbox "Linked account access" should be checked.

2. Enable a specific set of cost allocation tags.

   This can be done via "Billing and Cost Management" -> "Cost Allocation Tags".

   The tags that to be activated are:

   - 2i2c:hub-name
   - 2i2c.org/cluster-name
   - 2i2c.org/node-purpose
   - alpha.eksctl.io/cluster-name
   - kubernetes.io/cluster/<cluster_name>
   - kubernetes.io/created-for/pvc/name
   - kubernetes.io/created-for/pvc/namespace
```
````

`````

### 2. (optional) Backfill billing data

You can optionally backfill billing data to tags having been around for a while
but not enabled as cost allocation tags.

You can request this to be done once a day, and it takes a several hours to
process the request. Make a request through the AWS web console by navigating to
"Cost allocation tags" under "Billing and Cost Management", then from there
click the "Backfill tags" button.

### 3. Install `jupyterhub-cost-monitoring` Helm chart

In the cluster's `terraform/aws/projects/<cluster_name>.tf` file, set

```bash
enable_jupyterhub_cost_monitoring = true
```

The helm deployment is unconditionally enabled with jsonnet, unless explicitly overridden in the `config/clusters/<cluster_name>/support.values.yaml` file, and the configuration is automatically defined in the `helm-charts/support/values.jsonnet` file.

Finally deploy the support chart:

```bash
deployer deploy-support $CLUSTER_NAME
```

## Troubleshooting

If you don't see data in the cost monitoring dashboard, you may want to look to
ensure the `jupyterhub-cost-monitoring` deployment's pod is running in the support namespace, or if it reports errors in its logs.
