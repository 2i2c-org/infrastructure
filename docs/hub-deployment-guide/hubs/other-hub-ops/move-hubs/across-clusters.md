# Move a Hub across clusters

Moving hubs between clusters is possible, but requires manual steps
to ensure data is preserved.

## 1. Setup a new hub

Setup [a new hub](../../../topic/infrastructure/config.md) in the target cluster, mimicking
the config of the old hub as much as possible.

## 2. Copy home directories

Next, copy home directory contents from the old cluster to the new cluster.

```{note}
This might not entirely be necessary - if the source and target cluster
are in the same GCP Project / AWS Account, we can just re-use the same
home directory storage!
```

(nfs_servers)=
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
For long-running tasks, especially those running on a remote machine, we recommend using [`screen`](https://www.gnu.org/software/screen/manual/screen.html). Screen is a utility that allows starting `screen` sessions that can then be put to run in the background with the possibility of re-attaching to them. Processes running in `screen` will continue to run in the background even if you get disconnected.
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

The user directories can then be transferred in the same manner as [NFS Servers](nfs_servers) with the locations updated to be the following:

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
the ssh key provided to `eksctl` during cluster creation to
ssh into any worker node. Then `mount` the EFS instance manually and
do your modifications. This prevents needing to create another EC2
instance just for this.
```

### Azure Files

```{note}
You may be tempted to attach an existing NFS server across two clusters. However, this is not possible since Azure VMs cannot simultaneously exist in two virtual networks and each cluster will have it's own network.
```

We also use AzureFiles as in-cluster NFS storage. These are the steps to transfer the home directories from a NFS server located in another cluster, but in the same Azure subscription, into AzureFile NFS storage.

AzureFile needs to be mounted in the source NFS VM in order to copy the data.

1. Make sure AzureFile has access to the VNet in which the source NFS VM is in. Documentation on how to do that is can be found [here](https://docs.microsoft.com/en-us/azure/storage/files/storage-files-networking-endpoints?tabs=azure-portal#restrict-public-endpoint-access).

2. On the source NFS VM:
   1. Locate the private ssh key counterpart of the public one set for this cluster. The private key is usually encrypted with sops and stored into the repository where the infrastructure config of the cluster resides.

      ```bash
      sops -d secrets/ssh-key > secrets/ssh-key.unsafe
      ```
   2. Make sure `kubectl` is authenticated with the Azure cluster that hosts the source VM, as we'll be 'hopping' through it to access the NFS VM.
      * List available contexts:

        ```bash
        kubectl config get-contexts
        ```

      * If the desired context doesn't show up in the list above, then authenticate using:

        ```bash
        az aks get-credentials --name CLUSTER_NAME --resource-group RESOURCE_GROUP_NAME
        ```

      * Switch to using the desired context

        ```bash
        kubectl config use-context <the-desired-context>
        ```

   3. Ssh into the source NFS VM using the [`./terraform/proxycommand.py`](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure/proxycommand.py) script, passing it the private key from step 1, the authorized user to connect to the VM using this key pair (this is usually `hubadmin` or `hub-admin`, and can be found in the [terraform config](https://github.com/2i2c-org/infrastructure/tree/HEAD/terraform/azure/main.tf#L63) [`azurerm_kubernetes_cluster.linux_profile.admin_username`](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster#admin_username)), and the address of the NFS VM.
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

```{note}
If the total size of the home directories is considerable, then copying the files from one cluster to another might take a long time. So make sure you have enough time to perform this operation and check the transfer rates once the data transfer starts.

Tip: You can use [this script](https://github.com/2i2c-org/infrastructure/tree/HEAD/extra-scripts/rsync-active-users.py) that performs a parallel `rsync` of home directories for active users only.
```


## 3. Set up Grafana Dashboards for the new cluster
Make sure the new cluster has Grafana Dashboards deployed. If not, follow the steps in [](setup-grafana). Also, verify if the old cluster had Prometheus deployed and whether you also need to migrate that.

## 4. Take down the current hub
Delete the proxy service to make the hub unreacheable.

``` bash
kubectl delete svc proxy-public -n <old_prod_namespace>
```

```{note}
This is a disruptive operation, and will make the hub unusable until the remaining steps are performed and the new hub is ready. So make sure you have planned a migration down-time with the hub representatives.
```

## 5. Transfer the JupyterHub Database

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

## 6. Delete all user pods from the old cluster

This will kick out all users from the old hub and close any running user servers and kernels.

```bash
kubectl get pods -n <old_prod_namespace> --no-headers=true | awk '/jupyter/{print $1}' | xargs kubectl delete -n <old_prod_namespace> pod
```

## 7. Do one final copying of the home directories
This will catch all the user changes since the last rsync. However long this takes is the total amount of downtime we'll have.

## 8. Transfer DNS

Retrieve the external IP address for the `ingress-nginx` load balancer.

```bash
kubectl --namespace support get svc support-ingress-nginx-controller
```

Edit the existing DNS entry in NameCheap that matches the old hub domain and type in this external IP address.

This will move DNS from old cluster to new cluster, thus completing the move.

## 9. Cleanup the old cluster and NFS VM

Make sure to preserve any relevant information (such as hub logs) before tearing down the cluster and NFS VM.
