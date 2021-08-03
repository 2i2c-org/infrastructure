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

If you are working in a project that restricts the use of external IPs, there are a few extra steps to consider.
While the NFS server does not require an external IP address to do it's job, internet access is required to install the appropriate packages in the next section.
Therefore, we will temporarily deploy a [Cloud NAT](https://cloud.google.com/nat/docs) to grant internet access to our VM.

```{note}
Tutorials on this will mention setting up a firewall rule to allow SSH connections.
However, if you're in the situation of being restricted on external IPs, you likely deployed the cluster with the `enable_private_cluster` variable set to `true` which means there is already a firewall rule allowing SSH connections in place.
```

1. Create a Cloud Router instance for your region.
   We will assume `us-central1`.

   ```bash
   gcloud compute routers create nat-router-us-central1 \
     --network default \
     --region us-central1
   ```

2. Configure the routers for Cloud NAT

   ```bash
   gcloud compute routers nats create nat-config \
     --router-region us-central1 \
     --router nat-router-us-central1 \
     --nat-all-subnet-ip-ranges \
     --auto-allocate-nat-external-ips
   ```

3. Test your VM has access to the internet.
   SSH into it:

   ```bash
   gcloud compute ssh nfs-server-01 --tunnel-through-iap
   ```

   Use the `curl` command to make an outbound request:

   ```bash
   curl example.com
   ```

   This should print some raw html to your console.

## Setting up the NFS Server

Once your VM has been deployed, SSH into it so we can configure the NFS server.

```bash
gcloud compute ssh nfs-server-01
```

```{note}
Don't forget to add the `--tunnel-through-iap` flag if you deployed the VM **without** an external IP!
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

### Deleting the Cloud NAT resources

Once the NFS server is configured, the Cloud NAT resources can be deleted.

```bash
gcloud compute routers nats delete nat-config \
  --router nat-router-us-central1

gcloud compute routers delete nat-router-us-central1
```
