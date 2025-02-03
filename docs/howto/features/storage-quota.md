(howto:configure-storage-quota)=
# Configure per-user storage quotas

This guide explains how to enable and configure per-user storage quotas using the `jupyterhub-home-nfs` helm chart.

```{note}
Nest all config examples under a `basehub` key if deploying this for a daskhub.
```

## Creating a pre-provisioned disk

The in-cluster NFS server uses a pre-provisioned disk to store the users' home directories. We don't use a dynamically provisioned volume because we want to be able to reuse the same disk even when the Kubernetes cluster is deleted and recreated. So the first step is to create a disk that will be used to store the users' home directories.

For infrastructure running on AWS, we can create a disk through Terraform by adding a block like the following to the [`tfvars` file of the cluster](https://github.com/2i2c-org/infrastructure/tree/main/terraform/aws/projects):

```
ebs_volumes = {
  "staging" = {
    size        = 100  # in GB
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name": "staging" }
  }
}
```

This will create a disk with a size of 100GB for the `staging` hub that we can reference when configuring the NFS server.

Apply these changes with:

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

```{important}
At this point, it is also a good idea to enable [automatic backups of the the NFS server](howto:filesystem-backups:enable:aws) as well.
```

## Enabling `jupyterhub-home-nfs`

To be able to configure per-user storage quotas, we need to run an in-cluster NFS server using [`jupyterhub-home-nfs`](https://github.com/sunu/jupyterhub-home-nfs). This can be enabled by setting `jupyterhub-home-nfs.enabled = true` in the hub's values file (or the common values files if all hubs on this cluster will be using this).

`jupyterhub-home-nfs` expects a reference to an pre-provisioned disk.
You can retrieve the `volumeId` by checking the Terraform outputs:

```bash
terraform output
```

Here's an example of how to connect the volume to `jupyterhub-home-nfs` on AWS and GCP in the hub values file.

`````{tab-set}
````{tab-item} AWS
:sync: aws-key
```yaml
jupyterhub-home-nfs:
  enabled: true  # can be migrated to common values file
  eks:
    enabled: true  # can be migrated to common values file
    volumeId: vol-0a1246ee2e07372d0
```
````

````{tab-item} GCP
:sync: gcp-key
```yaml
jupyterhub-home-nfs:
  enabled: true  # can be migrated to common values file
  gke:
    enabled: true  # can be migrated to common values file
    volumeId: projects/jupyter-nfs/zones/us-central1-f/disks/jupyter-nfs-home-directories
```
````
`````

These changes can be deployed by running the following command:

```bash
deployer deploy $CLUSTER_NAME $HUB_NAME
```

Once these changes are deployed, we should have a new NFS server running in our cluster through the `jupyterhub-home-nfs` Helm chart. We can get the IP address of the NFS server by running the following commands:

```bash
# Authenticate with the cluster
deployer use-cluster-credentials $CLUSTER_NAME

# Retrieve the service IP
kubectl -n $HUB_NAME get svc ${HUB_NAME}-nfs-service
```

To check whether the NFS server is running properly, see the [Troubleshooting](#troubleshooting) section.

## Migrating existing home directories and switching to the new NFS server

See [](migrate-data) for instructions on performing these steps.

## Enforcing storage quotas

````{warning}
If you attempt to enforce quotas before having performed the migration, you may see the following error:

```bash
FileNotFoundError: [Errno 2] No such file or directory: '/export/$HUB_NAME'
```
````

Now we can set quotas for each user and configure the path to monitor for storage quota enforcement.

This can be done by updating `basehub.jupyterhub-home-nfs.quotaEnforcer` in the hub's values file. For example, to set a quota of 10GB for all users on the `staging` hub, we would add the following to the hub's values file:

```yaml
jupyterhub-home-nfs:
  quotaEnforcer:
    hardQuota: "10" # in GB
    path: "/export/staging"
```

The `path` field is the path to the parent directory of the user's home directory in the NFS server. The `hardQuota` field is the maximum allowed size of the user's home directory in GB.

To deploy the changes, we need to run the following command:

```bash
deployer deploy $CLUSTER_NAME $HUB_NAME
```

Once this is deployed, the hub will automatically enforce the storage quota for each user. If a user's home directory exceeds the quota, the user's pod may not be able to start successfully.

## Enabling alerting through Prometheus Alertmanager

Once we have enabled storage quotas, we want to be alerted when the disk usage of the NFS server exceeds a certain threshold so that we can take appropriate action.
To do this, we need to create a Prometheus rule that will alert us when the disk usage of the NFS server exceeds a certain threshold using Alertmanager.
We will then forward Alertmanager's alert to PagerDuty.

```{note}
Use these resource to learn more about [PagerDuty's Prometheus integration](https://www.pagerduty.com/docs/guides/prometheus-integration-guide/) and [Prometheus' Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/)
```

First, we need to enable the Prometheus exporter in the `jupyterhub-home-nfs` config so that the appropriate data is exported to Prometheus.
Add the following config to wherever `jupyterhub-home-nfs` is running, e.g., [see the `nasa-veda` config](https://github.com/2i2c-org/infrastructure/blob/15ded3ff6fa1ee51f2622f8c3b7f7e91283eefa5/config/clusters/nasa-veda/common.values.yaml#L315-L316).

```yaml
jupyterhub-home-nfs:
  prometheusExporter:
    enabled: true
```

First, we need to enable Alertmanager in the cluster's support values file (for example, [here's the one for the `nasa-veda` cluster](https://github.com/2i2c-org/infrastructure/blob/main/config/clusters/nasa-veda/support.values.yaml)).

```yaml
prometheus:
  alertmanager:
    enabled: true
```

Next, we need to create a Prometheus rule that will alert us when the disk usage of the NFS server exceeds a certain threshold. For example, to alert us when the disk usage of the NFS server exceeds 90% of the total disk size over a 15min period, we would add the following to the hub's support values file:

```yaml
prometheus:
  serverFiles:
    alerting_rules.yml:
      groups:
        # Duplicate this entry for every hub on the cluster that uses an EBS volume as an NFS server
        - name: <cluster_name> <hub_name> jupyterhub-home-nfs EBS volume full
          rules:
            - alert: <hub_name>-jupyterhub-home-nfs-ebs-full
              expr: node_filesystem_avail_bytes{mountpoint="/shared-volume", component="shared-volume-metrics", namespace="<hub_name>"} / node_filesystem_size_bytes{mountpoint="/shared-volume", component="shared-volume-metrics", namespace="<hub_name>"} < 0.1
              for: 15m
              labels:
                severity: critical
                channel: pagerduty
                cluster: <cluster_name>
              annotations:
                summary: "jupyterhub-home-nfs EBS volume full in namespace {{ $labels.namespace }}"
```

```{note}
The important variables to note here are:

- `expr`: This is what Prometheus will evaluate
- `for`: This is a duration over which Prometheus will collect data to evaluate `expr`
```

And finally, we need to configure Alertmanager to send alerts to PagerDuty.

```yaml
prometheus:
  alertmanager:
    enabled: true
    config:
      route:
        group_wait: 10s
        group_interval: 5m
        receiver: pagerduty
        repeat_interval: 3h
        routes:
          # Duplicate this entry for every hub on the cluster that uses an EBS volume as an NFS server
          - receiver: pagerduty
            match:
              channel: pagerduty
              cluster: <cluster_name>
              namespace: <hub_name>
```

```{note}
The important variables to understand here are:

- `group_wait`: How long Alertmanager will initially wait to send a notification to PagerDuty for a group of alerts
- `group_interval`: How long Alertmanager will wait to send a notification to PagerDuty for new alerts in a group for which an initial notification has already been sent
- `repeat_interval`: How long Alertmanager will wait to send a notification to PagerDuty again if it has already sent a successful notification
- `match`: These labels are used to group fired alerts together and is how we manage separate incidents per hub per cluster in PagerDuty

[Read more about these configuration options.](https://prometheus.io/docs/alerting/latest/configuration/#route)
```

## Increasing the size of the volume used by the NFS server

If the volume used by the NFS server is close to being full, we may need to increase the size of the volume. This can be done by following the instructions in the [Increase the size of an AWS EBS volume](howto:increase-size-aws-ebs) guide.

## Troubleshooting

### Checking the NFS server is running properly

To check whether the NFS server is running properly, we can run the following command in the NFS server pod in the nfs-server container:

```bash
showmount -e 0.0.0.0
```

If the NFS server is running properly, we should see the path to the NFS server's export directory. For example:

```bash
Export list for 0.0.0.0:
/export *
```

If we don't see the path to the export directory, the NFS server is not running properly and we need to check the logs for the NFS server pod.

### Debugging quota enforcement

We can check the current usage and quotas for each user by running the following command in the NFS server pod in the `enforce-xfs-quota` container:

```bash
xfs_quota -x -c 'report -N -p'
```

This should show us the list of directories being monitored for quota enforcement, and the current usage and quotas for each of the home directories.

If a user exceeds their quota, the user's pod will not be able to start successfully. A hub admin will need to free up space in the user's home directory to allow the pod to start, using [the `allusers` feature](topic:storage:allusers).
