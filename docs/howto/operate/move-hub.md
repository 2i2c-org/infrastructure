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
   server's `/home/ubuntu/.ssh/authorized_keys` file, so the target
   NFS server can open SSH connections to the source NFS server.
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
ubuntu@nfs-source-server-public-IP:/mnt/filestore/<hub-name> /mnt/filestore/<hub-name>
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

## Transfer DB

Copy `/srv/jupyterhub/jupyterhub.sqlite` file from old hub pod to new
hub's. This preserves user information, since they might be added via
the admin UI. The `kubectl cp` command might be used here, to copy
`jupyterhub.sqlite` file from old hub pod to your local machine, and
then to the new hub.

## Transfer DNS

Move DNS from old cluster to new cluster, thus completing the move.
