(howto:cost-monitoring:enable-aws)=
# Enable JupyterHub Cost Monitoring

The JupyterHub Cost Monitoring system consists of the [jupyterhub-cost-monitoring](https://github.com/2i2c-org/jupyterhub-cost-monitoring/) backend and Grafana cloud cost dashboards
that use the backend as a data source.

Checkout the [topic guide](topic:billing:cost-monitoring) for more information on the system.

## Steps

### 1. Enable cost allocation tags

Enabling cost allocation tags via terraform can be done for AWS
accounts that we have billing permissions for, but not for standalone accounts that communities manage themselves.

`````{tab-set}

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

````{tab-item} Member account (2i2c SSO)
:sync: member-2i2c

2i2c's AWS organization have all but one cost allocation tags activated already,
you only need to activate `kubernetes.io/cluster/<cluster name>` manually.

To do this, visit https://2i2c.awsapps.com/start/#/ and login to the
`2i2c-sandbox` account, then from [cost allocation tags] find and enable the tag
`kubernetes.io/cluster/<cluster name>`. If you can't find it and created the
cluster very recently, come back in a few hours and try again.

[cost allocation tags]: https://us-east-1.console.aws.amazon.com/billing/home?region=us-east-1#/tags
````

````{tab-item} Community-managed account without billing permissions
:sync: member-community

We can't do this ourselves, but we can communicate instructions to the community
on what they need to do in order to have this function.

Below is part of a message that could be used when communicating with a community
representative about this. Note that the message mentions `<cluster name>` as
part of a tag, update that to be the community's actual cluster name as listed
within a eksctl .jsonnet file.

```
In order for 2i2c to provide an overview cloud costs via a Grafana dashboard,
the following changes needs to be made in the AWS organization's management
account:

1. Declare that linked member accounts are allowed to access Cost Explorer.

   This can be done via "Billing and Cost Management" -> "Cost Management Preferences",
   where the checkbox "Linked account access" should be checked.

2. Enable a specific set of cost allocation tags.

   This can be done via "Billing and Cost Management" -> "Cost Allocation Tags".

   The tags that needs to be enabled to function as cost allocation tags are:

   - 2i2c:hub-name
   - 2i2c.org/cluster-name
   - 2i2c.org/node-purpose
   - alpha.eksctl.io/cluster-name
   - kubernetes.io/cluster/<cluster name>
   - kubernetes.io/created-for/pvc/name
   - kubernetes.io/created-for/pvc/namespace
```
````

`````

```{note}
The `kubernetes.io/created-for/pvc/namespace` is enabled even if its currently
not used by `jupyterhub-cost-monitoring`, as it could help us attribute cost for
storage disks dynamically provisioned in case that's relevant in the future.
```

### 2. (optional) Backfill billing data

You can optionally backfill billing data to tags having been around for a while
but not enabled as cost allocation tags.

You can request this to be done once a day, and it takes a several hours to
process the request. Make a request through the AWS web console by navigating to
"Cost allocation tags" under "Billing and Cost Management", then from there
click the "Backfill tags" button.

### 3. Install `jupyterhub-cost-monitoring` Helm chart

In the cluster's terraform variables, make sure the following is present:

```bash
enable_jupyterhub_cost_monitoring_iam = true
```

After applying this, look at the terraform output named `jupyterhub_cost_monitoring_k8s_sa_annotation`:

```bash
terraform output -raw jupyterhub_cost_monitoring_k8s_sa_annotation
```

Open the cluster's `support.values.yaml` file and update add a section like below, updating the `CLUSTER_NAME` and adding the service account annotation (key and value) from the terraform output.

```yaml
jupyterhub-cost-monitoring:
  enabled: true
  extraEnv:
    - name: CLUSTER_NAME
      value: openscapeshub
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::<aws_account_number>:role/jupyterhub_cost_monitoring_iam_role
```

Finally deploy the support chart:

```bash
deployer deploy-support $CLUSTER_NAME
```

## Troubleshooting

If you don't see data in the cost monitoring dashboard, you may want to look to
ensure the `jupyterhub-cost-monitoring` deployment's pod is running in the support namespace, or if it reports errors in its logs.
