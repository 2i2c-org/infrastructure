(migrate-data-external)=

# Transfer data between NFS servers on separate clusters

```{important}
This guide leverages features in the `jupyterhub-home-nfs` Helm chart, although the underlying tools do not have this dependence.
```

This documentation covers how to transfer data between NFS servers running on different clusters in a cloud-agnostic way. For simplicity and reliability, this guide focuses on using `rsync` over SSH to securely and reliably copy a filesystem between distinct NFS servers.

``````{note}
`rsync` can be performed in a forwards or reverse direction, e.g.

`````{tab-set}
````{tab-item} Forward
```bash
# Run on src
rsync /foo user@dst:/bar/
```
````
````{tab-item} Reverse
```bash
# Run on dst
rsync user@src:/foo /bar/
```
````
`````

For simplicity, we'll rsync in the forwards direction and run `rsync` from the _source_ container.

``````

(migrate-external:setup-dst)=

## Setting up the destination server

```{important}
Run this section on the destination cluster.
```

1. **Create a public-private key pair**  
   To securely communicate between the two file-servers, we must create a keypair:

   ```bash
   ssh-keygen -N "" -t ed25519 -f key
   ```

   This will create two files in the working directory, `key` and `key.pub`. From here on, we'll refer to the _contents_ of `key.pub` as `<PUBLIC-KEY-CONTENTS>`

2. **Deploy an OpenSSH server container**

   The [`linuxserver/openssh-server`](https://hub.docker.com/r/linuxserver/openssh-server) Docker image is a well-tested image that ships with an OpenSSH server. For simplicity, we will deploy this image as a container on both the source and destination `jupyterhub-home-nfs` deployments.[^simple]

   [^simple]: Although we only need an SSH server on _destination_ side in forward mode, this container also providers a generic shell environment that is nearly sufficient for performing an `rsync`.

   We can start by adding this image as an entry of `jupyterhub-home-nfs.extraContainers`. The configuration for the destination deployment is shown in [the following code block](migrate-external:values-dst), with the features required to run an SSH server emphasised:

   ```{code-block} yaml
   :name: migrate-external:values-dst
   :emphasize-lines: 5,6,15,16
   jupyterhub-home-nfs:
     extraContainers:
       - name: openssh-server
         image: linuxserver/openssh-server:latest
         ports:
           - containerPort: 2222
         volumeMounts:
           - mountPath: /export
             name: home-directories
         env:
           - name: PUID
             value: "1000"
           - name: PGID
             value: "1000"
           - name: PUBLIC_KEY
             value: <PUBLIC-KEY-CONTENTS>
   ```

   This configuration can then be deployed by running `deployer deploy <DEST-CLUSTER> <DEST-HUB>`.

3. **Install `rsync`**

   The container image described in [the `extraContainers` configuration](migrate-external:values-dst) does not natively include the `rsync` utility. We can remedy this by opening a shell with the following command:

   ```shell
   kubectl -n <DEST-HUB> exec -it deploy/storage-quota-home-nfs -c openssh-server -- /bin/sh
   ```

   As this image is based upon Alpine Linux, we can easily install `rsync` with

   ```bash
   apk add rsync
   ```

4. **Establish an ingress**

   To make the SSH server visible outside the cluster, we'll need to expose the container via a service:

   ```bash
   # Assume deployment is called storage-quota-home-nfs
   kubectl -n <DEST-HUB> expose --type LoadBalancer deploy storage-quota-home-nfs --port=2222 --name openssh-service
   ```

   We can now investigate the external IP `<SERVICE-IP>` associated with this service, and record it for later:

   ```bash
   kubectl -n <DEST-HUB> get service/openssh-service
   ```

## Setting up the source server

```{important}
Run this section on the source cluster.
```

1. **Deploy a file-transfer container**  
   We can add the same image used in [](migrate-external:setup-dst) as an entry of `jupyterhub-home-nfs.extraContainers`. The configuration for the source deployment is shown in [the following code block](migrate-external:values-src), with the specialisations for the source container emphasised:

   ```{code-block} yaml
   :name: migrate-external:values-src
   :emphasize-lines: 8
   jupyterhub-home-nfs:
     extraContainers:
       - name: openssh-server
         image: linuxserver/openssh-server:latest
         volumeMounts:
           - mountPath: /export
             name: home-directories
             readonly: true
         env:
           - name: PUID
             value: "1000"
           - name: PGID
             value: "1000"
   ```

   This configuration can then be deployed by running `deployer deploy <SRC-CLUSTER> <SRC-HUB>`.

2. **Provision the SSH private key**

   In order for the sender to be able to authorise with the receiver, we'll need to provision the environment with the private counterpart to the [public key that we created earlier](migrate-external:keypair). We can easily do this by writing it to a temporary file from the clipboard. In the source container, open a shell by running the following command:

   ```shell
   kubectl -n <SRC-HUB> exec -it deploy/storage-quota-home-nfs -c openssh-server -- /bin/sh
   ```

   Run the following, paste the key with {kbd}`Ctrl+V`, and then enter an EOF with {kbd}`Ctrl+D`

   ```bash
   cat > /tmp/key
   ```

   We must now define an SSH configuration entry and configure it with the appropriate IP address, port, and username. If you're using the image defined in this how-to guide, you'll only need to change the `HostName`:

   ```{code-block} shell
   :emphasize-lines: 3
   echo > ~/.ssh/config '
   Host receiver
       HostName <SERVICE-IP>
       Port 2222
       IdentityFile /tmp/key
       User linuxserver.io
       IdentitiesOnly yes
   '
   ```

3. **Install `rsync`**

   As we saw earlier, the container image described in [the `extraContainers` configuration](migrate-external:values-src) does not natively include the `rsync` utility. We can remedy this by opening a shell with the following command:

   ```shell
   kubectl -n <SRC-HUB> exec -it deploy/storage-quota-home-nfs -c openssh-server -- /bin/sh
   ```

   As this image is based upon Alpine Linux, we can easily install `rsync` with

   ```bash
   apk add rsync
   ```

(migrate-external:initial-sync)=

## Performing the initial sync

```{important}
Run this section on the source cluster.
```

Now we can use `rsync` in archive mode (preserving the important file attributes) and sync with the remote. Substitute `<SRC_HUB_NAME>` and `<DST-HUB-NAME>` with the names of the source and destination hubs. These names are used to determine the name of the home directory within the storage volume.

```shell
rsync -avh /export/<SRC-HUB>/ receiver:/export/<DST-HUB>/
```

## Performing the final sync

```{important}
Run this section on the source cluster.
```

Once an initial sync of the data has been performed, we can ensure that we've captured the true state of the disk by performing a final reconciliation sync. We will do this only once we are confident that there are no active sessions modifying the home storage, and that new sessions cannot be started. This may be ensured by:

1. Disabling the source ingress with `kubectl -n <SRC-HUB> delete ingress jupyterhub`.
2. Stopping existing user pods.

```{danger}
Stopping user pods is highly disruptive. Unless you're operating inside scheduled down-time, prefer to wait for the cluster activity to fall to zero. You can introduce a maintenance window overnight by disabling the spawner, and allowing existing sessions to terminate.
```

Now that we've cordoned off the storage, we can repeat the step performed in [](migrate-external:initial-sync) to copy only the modified files.

## Tearing down the transfer deployments

After copying the files between disks, we now can tear down the migration deployments.

1. First, delete the service created in [](migrate-external:setup-dst) by running the following in the destination hub context:
   ```shell
   kubectl -n <DST-HUB> delete service/openssh-service
   ```
2. Then, revert the changes to the JupyterHub `values.yaml` in [](migrate-external:setup-dst) and [](migrate-external:setup-src).
3. Finally, re-deploy both hubs.
