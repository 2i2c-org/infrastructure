# User home directory storage

All users on all the hubs get a home directory with persistent storage.

This is made available through cloud-specific filestores.

```{figure} ../../images/infrastructure-storage-layer.png
```

% The editable version of the diagram is here: https://docs.google.com/presentation/d/1zu7d1mXN6R32i124vtohNXVIpqO-goiY01KzWQsZsas/edit?usp=sharing

## Managed NFS Server setup

[Terraform](topic:terraform) is setup to provision managed NFS server using the following cloud specific implementations.

* GCP: Google Filestore
* Azure: Files
* AWS: Elastic File System

## NFS Client setup

For each hub, there needs to be the components described by the following subsections.

### Hub directory

A directory is created under the path defined by the `nfs.pv.baseShareName` cluster config.
Usually, this is `/homes` - for hubs that use the managed NFS provider for the cloud platform.

Created using the infrastructure described in the [terraform section](topic:terraform).


This the the base directory under which each hub has a directory ([`nfs.pv.baseShareName`](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L21)).
This is done through [a job](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/templates/nfs-share-creator.yaml) that's created for each deployment via [helm hooks](https://helm.sh/docs/topics/charts_hooks/) that will mount `nfs.pv.baseShareName`, and make sure the directory for the hub is present on the NFS server with appropriate permissions.

  ```{note}
  The NFS share creator job will be created pre-deploy, run, and cleaned up before deployment proceeds. Ideally, this would only happen once per hub setup - but we don't have a clear way to do that yet.
  ```

### Hub user mount

For each hub, [a PersistentVolumeClaim(PVC) and a PersistentVolume(PV)](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/templates/nfs.yaml) are created.
This is the Kubernetes *Volume* that refers to the actual storage on the NFS server.
The volume points to the hub directory created for the hub and user at `<hub-directory-path>/<hub-name>/<username>`
(this name is dynamically determined as a combination of `nfs.pv.baseShareName` and the current release name).
Z2jh then mounts the PVC on each user pod as a [volume named **home**](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/HEAD/jupyterhub/files/hub/jupyterhub_config.py#L277).

Parts of the *home* volume are mounted in different places for the users, as detailed below.

#### [User home directories](https://github.com/2i2c-org/infrastructure/blob/341b9408fc7a9a60ea81296d8a0e6eee85bd0498/helm-charts/basehub/values.yaml#L185-L187)

Z2jh will mount into `/home/jovyan` (the mount path) the contents of the path `<hub-directory-path>/<hub-name>/<username>` on the NFS storage server.
Note that `<username>` is specified as a `subPath` - the *subdirectory* **in the volume to mount** at that given location.

#### Shared directories

##### [`/home/jovyan/shared`](https://github.com/2i2c-org/infrastructure/blob/341b9408fc7a9a60ea81296d8a0e6eee85bd0498/helm-charts/basehub/values.yaml#L271-L274)

Mounted for **all users**, showing the contents of `<hub-directory-path>/<hub-name>/_shared`.
This mount is **`readOnly`** and users **can't** write to it.

##### [`/home/jovyan/shared-readwrite`](https://github.com/2i2c-org/infrastructure/blob/341b9408fc7a9a60ea81296d8a0e6eee85bd0498/helm-charts/basehub/values.yaml#L66-L68)

Mounted **just for admins**, showing the contents of `<hub-directory-path>/<hub-name>/_shared`.
This volumeMount is **NOT `readOnly`**, so admins can write to it.

```{note}
This feature comes from the [custom KubeSpawner](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L182) that the our community hubs use, that allows providing extra configuration for admin users only.
```

#### (Optional) The `allusers` directory

Can be mounted **just for admins**, showing the contents of `<hub-directory-path>/<hub-name>/`.
This `volumeMount` can be made `readOnly` if the following volume property is set: `readOnly: true`.
If it is not specified, then by default, it is **NOT `readOnly`**, so admins can write to it.
It's purpose is to give access to the hub admins to all the users home directory to read and/or modify.

```yaml
jupyterhub:
  custom:
    singleuserAdmin:
      extraVolumeMounts:
        - name: home
          mountPath: /home/jovyan/allusers
          # Uncomment the line below to make the directory readonly for admins
          # readOnly: true
```

#### A `shared-public` directory

Mounted for *all users* in a read/write fashion, for a rough sharing solution.
This is put in a different backing directory than what is used for the regular `shared` directory.

```{warning}
All users can see all other users' contents, modify and delete them!
Use this with a lot of caution.
```

A `shared-public` directory needs to be mounted on all home directories, and we need to modify our `initContainer` to make sure this is owned by the appropriate user.

```yaml
jupyterhub:
  singleuser:
    storage:
      extraVolumeMounts:
        - name: home
          mountPath: /home/jovyan/shared-public
          subPath: _shared-public
          readOnly: false
        - name: home
          mountPath: /home/jovyan/shared
          subPath: _shared
          readOnly: true
    initContainers:
      - name: volume-mount-ownership-fix
        image: busybox
        command:
          [
            "sh",
            "-c",
            "id && chown 1000:1000 /home/jovyan && chown 1000:1000 /home/jovyan/shared && chown 1000:1000 /home/jovyan/shared-public && ls -lhd /home/jovyan ",
          ]
        securityContext:
          runAsUser: 0
        volumeMounts:
          - name: home
            mountPath: /home/jovyan
            subPath: "{username}"
          # Mounted without readonly attribute here,
          # so we can chown it appropriately
          - name: home
            mountPath: /home/jovyan/shared
            subPath: _shared
          - name: home
            mountPath: /home/jovyan/shared-public
            subPath: _shared-public
```
