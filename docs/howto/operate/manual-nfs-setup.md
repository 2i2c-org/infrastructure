# Manually setup NFS Server for a cluster

This guide describes the manual steps required for setting up a NFS server to store users' home directories on the hub.

## Deploy the host Virtual Machine

We need to first deploy a small virtual machine with a persistent disk that will host the NFS server.
Using `gcloud`, the command is:

```bash
gcloud compute instances create nfs-server-01 \
--image=ubuntu-2004-focal-v20210720 \
--image-project=ubuntu-os-cloud \
--machine-type=g1-small \
--boot-disk-device-name=nfs-server-01 \
--boot-disk-size=100GB \
--boot-disk-type=pd-standard
```

````{note}
To find the values of `--image` and `--image-project`, run the following:

```bash
gcloud compute images list
```

Add `| grep ubuntu` to filter for Ubuntu images.

You can then check the image suits your needs by running:

```bash
gcloud computer images describe IMAGE_NAME --project=IMAGE_PROJECT
```
````

### Deploying a host VM with no External IP

TBA

## Setting up the NFS Server

Once your VM has been deployed, SSH into it so we can configure the NFS server.

```bash
gcloud compute ssh nfs-server-01
```

1. Install the dependencies

   ```bash
   sudo apt update
   sudo apt install nfs-kernel-server nfs-common xfsprogs
   ```

2. Create the appropriate directory

   ```bash
   sudo mkdir -p /export/home-01
   ```

3. Set the appropriate permissions on the directory

   ```bash
   sudo chmod -R 0700 /export/
   sudo chown -R 1000 /export/
   ```

4. Create the exports rule in the file `/etc/exports`

   ```bash
   sudo nano /etc/exports  # Create the file
   ```

   ```bash
   /export/home-01 10.0.0.0/8(all_squash,anonuid=1000,anongid=1000,no_subtree_check,rw,sync)  # Add this line to the bottom of the file
   ```

5. Run the export command

   ```bash
   sudo exportfs
   ```
