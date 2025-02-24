(howto:increase-disk-size)=
# Increase the size of a disk storing home directories

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
    size        = 100  # in GB. Increase this!
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
    size        = 100  # in GB. Increase this!
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

Once terraform has successfully applied, we also need to grow the size of the filesystem.

1. Run `deployer use-cluster-credentials $CLUSTER_NAME` to gain `kubectl` access to the cluster
1. Run `kubectl -n $HUB_NAME get pods` to find the NFS deployment pod name. It should look something like `${HUB_NAME}-nfs-deployment-<HASH>`.
1. Exec into the the quota enforcer container: `kubectl -n $HUB_NAME exec -it $POD_NAME -c enforce-xfs-quota -- /bin/bash`
1. Run `df -h` to find out where the directory is mounted, it's current size, and if that size reflects what you just deployed with terraform or not. The directory is _usually_ under `/export`, but is not guaranteed.
1. Run `xfs_growfs $DIR_NAME` to resize the directory
1. Re-run `df -h` to confirm new size
