(migrate-data-external)=

# Transfer data between NFS servers on separate clusters

This documentation covers how to transfer data between NFS servers running on different clusters in a cloud-agnostic way. For simplicity and reliability, this guide focuses on using `rsync` over SSH to securely and reliably copy a filesystem between distinct NFS servers.

```{important} This guide requires `jupyterhub-home-nfs`

This guide leverages features in the `jupyterhub-home-nfs` Helm chart, although the underlying tools do not have this dependence.

```

(migrate-external:keypair)=
## Create a public-private key pair
To securely communicate between the two file-servers, we must create a keypair:
```bash
ssh-keygen -N "" -t ed25519 -f key
```

This will create two files in the working directory, `key` and `key.pub`. From here on, we'll refer to the _contents_ of `key.pub` as `<PUBLIC-KEY-CONTENTS>`

(migrate-external:deploy-container)=

## Deploy a file-transfer container

``````{note} Rsync direction
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

The [`linuxserver/openssh-server`](https://hub.docker.com/r/linuxserver/openssh-server) Docker image is a well-tested image that ships with an OpenSSH server. For simplicity, we will deploy this image as a container on both the source and destination `jupyterhub-home-nfs` deployments, as although we only need an SSH server on _destination_ side in forward mode, this container also providers a generic shell environment that is nearly sufficient for performing an `rsync`.

We can start by adding this image as an entry of `jupyterhub-home-nfs.extraContainers`. Both the source and destination deployments have slightly different requirements:

- The source deployment only requires read-only access to the home directory filesystem
- The receiver is the only container that needs to know the public key of the sender.

As such, we'll deploy two slightly different configurations, whose differences are emphasised below.

`````{tab-set}
````{tab-item} Source
```{code-block} yaml
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
````
````{tab-item} Destination
```{code-block} yaml
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
````
`````

These configurations can then be deployed by running the `deployer deploy <CLUSTER_NAME> <HUB_NAME>` **for both hubs**.

(migrate-external:ingress)=

## Establish an ingress

```{important}
Run this section on the destination cluster.
```

In order to connect to the destination, we'll need to expose the SSH server container via a service:

```bash
# Assume deployment is called storage-quota-home-nfs
kubectl -n <DEST-HUB> expose --type LoadBalancer deploy storage-quota-home-nfs --port=2222 --name openssh-service
```

We can now investigate the external IP `<SERVICE-IP>` associated with this service, and record it for later:

```bash
kubectl -n <DEST-HUB> get service/openssh-service
```

(migrate-external:provision-rsync)=

## Install `rsync` on each container

```{important}
Run this section on the source _and_ destination clusters.
```

The container image described in [](migrate-external:deploy-container) does not natively include the `rsync` utility. In each container, open a shell by running the following command:

```shell
kubectl -n <HUB> exec -it deploy/storage-quota-home-nfs -c openssh-server -- /bin/sh
```

As this image is based upon Alpine Linux, we can easily install it with

```bash
apk add rsync
```

This step must be performed on _both_ containers.

(migrate-external:provision-key)=

## Configure source SSH configuration

```{important}
Run this section on the source cluster.
```

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

(migrate-external:initial-sync)=
## Perform the initial sync

```{important}
Run this section on the source cluster.
```

Now we can use `rsync` in archive mode (preserving the important file attributes) and sync with the remote. Substitute `<SRC_HUB_NAME>` and `<DST-HUB-NAME>` with the names of the source and destination hubs. These names are used to determine the name of the home directory within the storage volume.

```shell
rsync -avh /export/<SRC-HUB>/ receiver:/export/<DST-HUB>/
```

## Disable the source ingress

```{important}
Run this section on the source cluster.
```

Once an initial sync of the data has been performed, we can ensure that we've captured the true state of the disk by performing a final reconciliation sync. We will do this only once we are confident that there are no active sessions modifying the home storage, and that new sessions cannot be started. This may be ensured by:
1. Disabling the source ingress with `kubectl -n <SRC-HUB> delete ingress jupyterhub`. 
2. Stopping existing user pods.

```{danger}
Stopping user pods is highly disruptive. Unless you're operating inside scheduled down-time, prefer to wait for the cluster activity to fall to zero. Youc an introduce a maintenance window overnight by disabling the spawner, and allowing existing sessions to terminate.
```

Now that we've cordoned off the storage, we can repeat the step performed in [](migrate-external:initial-sync) to copy only the modified files.

## Tear down the sync deployment
After copying the files between disks, we now can tear down the migration deployment. 

1. First, delete the service created in [](migrate-external:ingress) by running the following in the destination hub context:
   ```shell 
   kubectl -n <DST-HUB> delete service/openssh-service
   ```
2. Then, revert the configuration changes in [](migrate-external:deploy-container).
3. Finally, re-deploy both hubs.
