(howto:increase-disk-size)=
# Increase the size of a disk storing home directories

## Procedure

```bash
export CLUSTER_NAME=<cluster-name>;
export HUB_NAME=<hub-name>
```

To increase the size of a disk storing users' home directories, we need to increase its size in the [tfvars file of the cluster](https://github.com/2i2c-org/infrastructure/tree/main/terraform/)

`````{tab-set}
````{tab-item} AWS
```
ebs_volumes = {
  "staging" = {
    size        = 100  # in GiB. Increase this!
    type        = "gp3"
    name_suffix = "staging"
    tags        = { "2i2c:hub-name": "staging" }
  }
}
```
````
````{tab-item} GCP
```
persistent_disks = {
  "staging" = {
    size        = 100  # in GiB. Increase this!
    name_suffix = "staging"
  }
}
```
````
`````

After updating the tfvars file, we need to plan and apply the changes using terraform:

```bash
terraform workspace select $CLUSTER_NAME
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

```{warning}
The size of a disk can **only** be increased, *not* decreased.
```

Once terraform has successfully applied, we also need to grow the size of the filesystem with `xfs`.

1. Run `deployer use-cluster-credentials $CLUSTER_NAME` to gain `kubectl` access to the cluster
1. Run `kubectl -n $HUB_NAME get pods` to find the NFS deployment pod name. It should look something like `${HUB_NAME}-nfs-deployment-<HASH>`.
1. Exec into the the quota enforcer container: `kubectl -n $HUB_NAME exec -it $POD_NAME -c enforce-xfs-quota -- /bin/bash`
1. Run `df -h` to find out where the directory is mounted, it's current size prior to the `terraform apply`. The mounted directory is _usually_ under `/export`, but is not guaranteed.
1. Run `xfs_growfs $DIR_NAME` to resize the directory to the new size specified in the tfvars file. Replace `$DIR_NAME` with the _mounted_ directory you found in the previous step.
1. Re-run `df -h` to confirm the new size

## Community communication

Increasing the size of a storage disk has cost implications. Downsizing the volume is also a [complicated process](howto:decrease-size-gcp-filestore).
Please let the community know that we've performed an emergency resize using an email thread on FreshDesk after such resize has happened.

<details open>
<summary>Email template</summary>
<br>

> Dear all,
> 
> The home directory disk capacity for the <$CLUSTER_NAME> <$HUB_NAME> was close to its maximum limit.
> We have increased the disk so that now there is between 10% to 15% free space remaining.
> Recommended actions:
> 
> 1. Instruct users to delete any unused files from their home directories (saves cloud costs)
> 
> OR
> 
> 2. Instruct us to increase the home directory disk capacity in case you are expecting more of such increased usage (incurs cloud costs)
> 
> You can make use of the Grafana Dashboard *JupyterHub Default Dashboards >
> Home Directory Usage Dashboard* to get an overview of home directory usage per-user:
> 
> <$GRAFANA_URL>
</details>