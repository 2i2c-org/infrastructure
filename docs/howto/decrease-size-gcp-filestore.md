(howto:decrease-size-gcp-filestore)=
# Decrease the size of a GCP Filestore

Filestores deployed using the `BASIC_HDD` tier (which we do by default) support _increasing_ their size, but **not** _decreasing_ it.
Therefore when we talk about "decreasing the size of a GCP filestore", we are actually referring to creating a brand new filestore of the desired smaller size, copying all the files across from the larger filestore, and then deleting the larger filestore.

This document details how to proceed with that process.

```bash
export CLUSTER_NAME="<cluster-name>"
export HUB_NAME="<hub-name>"
```

## 1. Create a new filestore

Navigate to the `terraform/gcp` folder in the `infrastructure` repository and open the relevant `projects/<cluster-name>.tfvars` file.

Add another filestore definition to the file with config that looks like this:

```
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

## 2. Create a VM

In the GCP console of the project you are working in, [create a VM](https://console.cloud.google.com/compute/instances) by clicking the "Create instance" button at the top of the page.

- It is helpful to give the VM a name, such as `nfs-copy-vm`, so you can identify it
- Make sure you create the VM in the same region and/or zone as the cluster (you can find this info in the `tfvars` file)
- Choose an instance like an `e2-standard-8` which has 8 CPUs and 32GB memory
- Under the "Boot disk" section, increase the disk size to 500GB (this can always be changed later) and swap the operating system to Ubuntu

Once the VM has been created, click on it from the list of instances, and then ssh into it by clicking the ssh button at the top of the window.
This will open a new browser window.

## 3. Attach source and destination filestores to the VM[^1]

[^1]: <https://cloud.google.com/filestore/docs/mounting-fileshares>

First we need to install the NFS software:

```bash
sudo apt-get -y update &&
sudo apt-get install nfs-common
```

````{note}
If this fails, you may also need to install `zip` to extract the archive.

```bash
sudo apt-get install zip
```
````

We then make two folders which will serve as the mount points for the filestores:

```bash
sudo mkdir -p src-fs
sudo mkdir -p dest-fs
```

Mount the two filestores using the `mount command`

```bash
sudo mount -o rw,intr <ip-address>:/<file-share> <mount-point-folder>
```

`<file-share>` should always be `homes` and the `<ip-address>` for both filestores can be found on the [filestore instances page](https://console.cloud.google.com/filestore/instances).

You can confirm that the filestores were mounted successfully by running:

```bash
df -h --type=nfs
```

And the output should contain something similar to the following:

```bash
Filesystem        Size    Used  Avail  Use%  Mounted on
10.0.1.2:/share1  1018G   76M   966G   1%    /mnt/render
10.0.2.2:/vol3    1018G   76M   966G   1%    /mnt/filestore3
```

## 4. Copy the files from the source to the destination filestore

First of all, start a [screen session](https://linuxize.com/post/how-to-use-linux-screen/) by running `screen`.
This will allow you to close the browser window containing your ssh connection to the VM without stopping the copy process.

Begin copying the files from the source to the destination filestore with the following `rclone` command:

```bash
sudo rclone sync --multi-thread-streams=12 --progress --links src-fs dest-fs
```

Depending on the size of the filestore, this could take anywhere from hours to days!

```{admonition} screen tips
:class: tip

To disconnect your `screen` session, you can input {kbd}`Ctrl` + {kbd}`A`, then {kbd}`D` (for "detach").

To reconnect to a running `screen` session, run `screen -r`.

Once you have finished with your `screen` session, you can kill it by inputting {kbd}`Ctrl` + {kbd}`A`, then {kbd}`K` and confirming.
```

## 5. Use the new filestore IP address in all relevant hub config files

Once the initial copy of the files has completed, we can begin the process of updating the hubs to use the new filestore IP address.
It is best practice to begin with the `staging` hub before moving onto any production hubs.

At this point it is useful to set up two terminal windows:

- One terminal with `deployer use-cluster-credentials $CLUSTER_NAME` executed to run `kubectl commands
- Another terminal to run `deployer deploy $CLUSTER_NAME $HUB_NAME`

You should also have the browser window with the ssh connection to the VM handy to re-run the file copy command.

1. **Check there are no active users on the hub.**
   You can check this by running:
   ```bash
   kubectl --namespace $HUB_NAME get pods -l "component=singleuser-server"
   ```
   If no resources are found, you can proceed to the next step.
1. **Make the hub unavailable by deleting the `proxy-public` service.**
   ```bash
   kubectl --namespace $HUB_NAME delete svc proxy-public
   ```
1. **Re-run the `rclone` command on the VM.**
   This process should take much less time now that the initial copy has completed.
1. **Delete the `PersistentVolume` and all dependent objects.**
   `PersistentVolumes` are _not_ editable, so we need to delete and recreate them to allow the deploy with the new IP address to succeed.
   Below is the sequence of objects _dependent_ on the pv, and we need to delete all of them for the deploy to finish.
   ```bash
   kubectl delete pv ${HUB_NAME}-home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pvc home-nfs --wait=false
   kubectl --namespace $HUB_NAME delete pod -l component=shared-dirsize-metrics
   kubectl --namespace $HUB_NAME delete pod -l component=shared-volume-metrics
   ```
1. **Update `nfs.pv.serverIP` values in the `<hub-name>.values.yaml` file.**
1. **Run `deployer deploy $CLUSTER_NAME $HUB_NAME`.**
   This should also bring back the `proxy-public` service and restore access.
   You can monitor progress by running:
   ```bash
   kubectl --namespace $HUB_NAME get pods --watch
   ```

Repeat this process for as many hubs as there are on the cluster, remembering to update the value of `$HUB_NAME`.

Open and merge a PR with these changes so that other engineers cannot accidentally overwrite them.

We can now delete the VM we created to mount the filestores.

## 6. Decommission the previous filestore

Back in the `terraform/gcp` folder and `<cluster-name>.tfvars` file, we can delete the definition of the original filestore.

You also need to temporarily comment out the [`lifecycle` rule in the `storage.tf` file](https://github.com/2i2c-org/infrastructure/blob/1c8cb3ae787839eaab8b2dd21d49d33090176a05/terraform/gcp/storage.tf#L9-L13), otherwise the old filestore is prevented from being destroyed.

Plan and apply these changes, ensuring only the old filestore will be destroyed:

```
terraform plan -var-file=projects/$CLUSTER_NAME.tfvars
terraform apply -var-file=projects/$CLUSTER_NAME.tfvars
```

Open and merge a PR with these changes - but **DO NOT** commit the `storage.tf` file, you can discard those changes.

Congratulations! You have decreased the size of a GCP Filestore!
