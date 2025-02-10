(howto:increase-size-aws-ebs)=
# Increase the size of an AWS EBS volume

```bash
export CLUSTER_NAME=<cluster-name>;
export HUB_NAME=<hub-name>
```

To increase the size of an AWS EBS volume, we need to increase the size of the EBS volume in the [tfvars file of the hub](https://github.com/2i2c-org/infrastructure/tree/main/terraform/aws/projects):

For example, to increase the size of the EBS volume used by `jupyterhub-home-nfs` for the `staging` hub in the `nasa-veda` cluster, we would increase the `size` parameter in the `ebs_volumes` block for the `staging` hub in the [tfvars file for the `nasa-veda` cluster](https://github.com/2i2c-org/infrastructure/blob/main/terraform/aws/projects/nasa-veda.tfvars).

After updating the tfvars file, we need to plan and apply the changes using terraform:

```bash
cd terraform/aws
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

```{note}
The size of an EBS volume can only be increased, not decreased.
```

Once terraform has successfully applied, we also need to grow the size of the filesystem.

1. Run `deployer use-cluster-credentials $CLUSTER_NAME` to gain `kubectl` access to the cluster
1. Run `kubectl -n $HUB_NAME get pods` to find the NFS deployment pod name. It should look something like `${HUB_NAME}-nfs-deployment-<HASH>`.
1. Exec into the the quota enforcer container: `kubectl -n $HUB_NAME exec -it $POD_NAME -c enforce-xfs-quota -- /bin/bash`
1. Run `df -h` to find out where the directory is mounted, it's current size, and if that size reflects what you just deployed with terraform or not. The directory is _usually_ under `/export`, but is not guaranteed.
1. Run `xfs_growfs $DIR_NAME` to resize the directory
1. Re-run `df -h` to confirm new size
