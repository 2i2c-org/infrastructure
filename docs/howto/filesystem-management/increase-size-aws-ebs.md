(howto:increase-size-aws-ebs)=
# Increase the size of an AWS EBS volume

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
