# Move a Hub across clusters

Moving hubs between clusters is possible, but requires manual steps
to ensure data is preserved.

## Setup a new hub

Setup [a new hub](../../topic/config.md) in the target cluster, mimicking
the config of the old hub as much as possible.

## Copy home directories

Next, copy home directory contents from the old cluster to the new cluster.

```{note}

This might not entirely be necessary - if the source and target cluster
are in the same GCP Project / AWS Account, we can just re-use the same
home directory storage!
```

### NFS Servers

Primarily used with GKE right now.

1. SSH into **both** the target server and source server and then enable the `ubuntu` user on **both** servers with `sudo su ubuntu`.
   This will ensure that the keys we are about to create will be assigned to the correct user.
2. In the target NFS server, create a new ssh key-pair, with
   `ssh-keygen -f nfs-transfer-key`
3. Append the public key `nfs-transfer-key.pub` to the source NFS
   server's `/home/ubuntu/.ssh/authorized_keys` file. This way, the target
   NFS server will be able to open SSH connections to the source NFS server.
4. Copy the NFS home directories from the source NFS server to
   the target NFS server, making sure that the NFS exports locations
   match up appopriately. For example, if the source NFS server has
   home directories for each hub stored in `/export/home-01/homes`,
   and the target NFS server also has hub home directories stored under
   `/export/home-01/homes`, you can `scp` the contents across with:

   ```bash
   scp -p -r -i nfs-transfer-key ubuntu@nfs-source-server-public-IP:/export/home-01/homes/<hub-name> /export/home-01/homes/<hub-name>
   ```

   This makes sure the target is owned by the `ubuntu` user, which has
   uid `1000`. Our user pods run as uid `1000`, so this makes sure they
   can mount their home directories.

As an alternative to `scp` you can use `rsync` as follows:

```bash
rsync -e 'ssh -i nfs-transfer-key' -rouglvhP ubuntu@nfs-source-server-public-IP:/export/home-01/homes/<hub-name>/ /export/home-01/homes/<hub-name>/
```

```{note}
The trailing slashes are important to copy the contents of the directory, without copying the directory itself.
```

See the [`rsync` man page](https://ss64.com/bash/rsync.html) to understand these options.

```{note}
For long-running tasks, especially those ran on a remote machine, we recommend using [`screen`](https://www.gnu.org/software/screen/manual/screen.html). Screen is an utility that allows starting `screen` sessions that can then be put to run in the background with the possiblity of re-attaching to them. Processes running in `screen` will continue to run in the background even if you get disconnected.
```

### GCP Filestores

We also use GCP Filestores as in-cluster NFS storage and can transfer the home directories between them in a similar fashion to the NFS servers described above.

The filestores must be mounted in order to be accessed.

1. Create VMs in the projects of the source and target filestores.
2. For **both** filestores, get the server address from the [GCP console](https://cloud.google.com/filestore/docs/mounting-fileshares).
3. On each VM for the source and target filestores:
   1. Install `nfs-common`:
      ```bash
      sudo apt-get -y update && sudo apt-get -y install nfs-common
      ```
   2. Create a mount point:
      ```bash
      sudo mkdir -p /mnt/filestore
      ```
   3. Mount the Filestore:
      ```bash
      sudo mount SERVER_ADDRESS /mnt/filestore
      ```

The user directories can then be transferred in the same manner as [NFS Servers](#nfs-servers) with the locations updated to be the following:

```bash
<your_scp_or_rsync_command> ubuntu@nfs-source-server-public-IP:/mnt/filestore/<hub-name> /mnt/filestore/<hub-name>
```

### EFS

[AWS DataSync](https://aws.amazon.com/datasync/)
([docs](https://docs.aws.amazon.com/datasync/latest/userguide/getting-started.html))
can copy files between EFS volumes in an AWS account. The [quickstart] Once the
source & dest EFS instances are created, create a DataSync instance in the the
VPC, Subnet and Security Group that have access to the EFS instance (you can
find these details in the 'Network' tab of the EFS page in the AWS Console). Set
the transfer to hourly, but immediately manually start the sync task. Once the
data is transfered over and verified, switch the EFS used in the hub config.
Remember to delete the datasync instance soon after - or it might incur extra
charges!

```{note}
If you need to modify the directory structure on the EFS instance, use
the ssh key provided to `kops` or `eksctl` during cluster creation to
ssh into any worker node. Then `mount` the EFS instance manually and
do your modifications. This prevents needing to create another EC2
instance just for this.
```

### Azure Files

```{note}
The exception: even if the source and target cluster are in the same Azure subscription, re-using the same home directory storage might prove more difficult than copying files from one storage to the other.
```

We also use AzureFiles as in-cluster NFS storage. These are the steps to transfer the home directories between a NFS server located in another cluster, but in the same Azure subscription with an AzureFile NFS storage.

AzureFile needs to be mounted in the source NFS VM in order to copy the data.

1. Make sure AzureFile has access to the VNet in which the source NFS VM is in. Documentation on how to do that is can be found [here](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-networking-endpoints?tabs=azure-portal#restrict-public-endpoint-access).

2. On the source NFS VM:
   1. Locate the private ssh key counterpart of the public one set for this cluster. The private key is usually encrypted with sops and stored into the repository where the infrastructure config of the cluster resides.
      ```bash
      sops -d secrets/ssh-key > secrets/ssh-key.unsafe
      ```
   2. Make sure `kubectl` is set to talk to the Azure cluster, that host the source VM, as we'll be 'hopping' through it to access the NFS VM.
      ```bash
      kubectl config use-context <the-desired-context>
      ```
   3. Ssh into the source NFS VM using the [`./terraform/proxycommand.py`](https://github.com/2i2c-org/infrastructure/blob/master/terraform/azure/proxycommand.py) script, passing it the private key from step 1, the authorized user to connect to the VM using this key pair (this is usually `hubadmin` or `hub-admin`, and can be found in the terraform config `azurerm_kubernetes_cluster.linux_profile.admin_username`), and the address of the NFS VM.
      ```bash
      ssh -i secrets/ssh-key.unsafe -o 'ProxyCommand=./terraform/proxycommand.py %h %p' <admin-username>@<nfs-server-address>
      ```

3. Mount AzureFile onto the sourcec NFS VM with the following commands (run inside the NFS VM):
   1. Create a mount point:
      ```bash
      sudo mkdir -p /mnt/new-nfs
      ```
   2. Mount the Filestore:
      ```bash
      sudo mount -t nfs 2i2cutorontohubstorage.file.core.windows.net:/2i2cutorontohubstorage/homes /mnt/new-nfs -o vers=4,minorversion=1,sec=sys
      ```
   3. Create a subdirectory to store the data, called `prod`. This means that user's home dirs that we will be copying will not be available on the `staging` hub, but only for the `prod` hub. This is to protect the user data in case the staging hub gets breached.
      ```bash
      sudo mkdir /mnt/new-nfs/prod
      sudo chown 1000:1000 /mnt/new-nfs/prod
      ```

4. Start transferring the user directories:
   From within the source NFS VM:
   ```bash
   <your_scp_or_rsync_command> <homes-directory-location-on-the-source-nfs-server> /mnt/new-nfs/prod/
   ```

## Transfer the JupyterHub Database

```{note}
This step is only required if users have been added to a hub manually, using the admin panel.
In cases where the auth is handled by an external service, e.g. GitHub, the hub database is flexible enough to update itself with the new information.
```

This step preserves user information, since they might be added via the admin UI.

1. Copy the `/srv/jupyterhub/jupyerhub.sqlite` file from the old hub pod locally.

   ```bash
   kubectl --namespace OLD_NAMESPACE cp -c hub OLD_HUB_POD_NAME:/srv/jupyterhub/jupyterhub.sqlite ./
   ```

2. Transfer the local copy of the `jupyterhub.sqlite` file to the new hub pod

   ```bash
   kubectl --namespace NEW_NAMESPACE cp -c hub ./jupyterhub.sqlite NEW_HUB_POD_NAME:/srv/jupyterhub/jupyterhub.sqlite
   ```

## Transfer DNS

Move DNS from old cluster to new cluster, thus completing the move.
