(howto:decrease-size-gcp-filestore)=
# Resize a GCP Filestore down

Filestores deployed using the `BASIC_HDD` tier (which we do by default) support _increasing_ their size, but **not** _decreasing_ it.
Therefore when we talk about "decreasing the size of a GCP filestore", we are actually referring to creating a brand new filestore of the desired smaller size, copying all the files across from the larger filestore, and then deleting the larger filestore.

This document details how to proceed with that process.

```bash
export CLUSTER_NAME="<cluster-name>"
export HUB_NAME="<hub-name>"
```

## Create a new filestore

Navigate to the `terraform/gcp` folder in the `infrastructure` repository and open the relevant `projects/<cluster-name>.tfvars` file.

Add another filestore definition to the file with config that looks like this:

```hcl
filestores = {
    "filestore" : {  # This first filestore instance should already be present
        capacity_gb: <larger capacity in GB>
    },
    "filestore_b" : {  # This is the second filestore we are adding
        name_suffix : "b",  # Or something similar
        capacity_gb : <desired, smaller capacity in GB>  # Or remove entirely to use the default of 1GB
    }
}
```

We add a `name_suffix` to avoid reusing the name the first filestore was given.

Plan and apply these changes, ensuring only the new filestore is created and nothing else is affected.

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

```{note}
If filestore backups are enabled for this cluster, don't forget to add the name
of the new filestore to the cluster's support values file, following
[the instructions](howto:filesystem-backups:enable:gcp).
```

Open a PR and merge these changes so that other engineers cannot accidentally overwrite them.

## Migrating the data and switching to the new filestore

See [](data-transfer) for instructions on how to perform these steps.

## Decommission the previous filestore

Back in the `terraform/gcp` folder and `<cluster-name>.tfvars` file, we can delete the definition of the original filestore.

You also need to temporarily comment out the [`lifecycle` rule in the `storage.tf` file](https://github.com/2i2c-org/infrastructure/blob/1c8cb3ae787839eaab8b2dd21d49d33090176a05/terraform/gcp/storage.tf#L9-L13), otherwise the old filestore is prevented from being destroyed.

Plan and apply these changes, ensuring only the old filestore will be destroyed:

```bash
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

Open and merge a PR with these changes - but **DO NOT** commit the `storage.tf` file, you can discard those changes.

Congratulations! You have decreased the size of a GCP Filestore!
