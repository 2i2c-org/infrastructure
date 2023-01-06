# User home directory storage

All users on all the hubs get a home directory with persistent storage. 

This is made available through cloud-specific filestores and **sometimes** through a manually-managed Network File System [(NFS)](https://en.wikipedia.org/wiki/Network_File_System) (usually this is the case on GCP clusters that are very price sensitive).

```{figure} ../../images/infrastructure-storage-layer.png
```

% The editable version of the diagram is here: https://docs.google.com/presentation/d/1zu7d1mXN6R32i124vtohNXVIpqO-goiY01KzWQsZsas/edit?usp=sharing


## NFS Server setup - only for manually managed servers

```{warning}
No longer the default option!

Use this as a last resort only on GCP clusters that are very price sensitive.
Use the cloud-specific filestore as default instead.

Checkout https://infrastructure.2i2c.org/en/latest/howto/operate/manual-nfs-setup.html#manually-setup-an-nfs-server.
```

Some of the 2i2c clusters has a NFS server that is usually located at `nfs-server-01`. This is currently hand configured, so it might change in the future. This NFS Server has a [persistent disk](https://cloud.google.com/persistent-disk) that's independent from rest of the VM (it can be grown / snapshotted independently). This disk is mounted inside the NFS server at `/export/home-01` (for the home directories of users) and is made available via NFS to be mounted by everything in the cluster, via [`/etc/exports`](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/5/html/deployment_guide/s1-nfs-server-config-exports):

```
/export/home-01 10.0.0.0/8(all_squash,anonuid=1000,anongid=1000,no_subtree_check,rw,sync)
```

```{note}
To SSH into the NFS server run:

    gcloud compute ssh nfs-server-01 --zone=us-central1-b
```

## NFS Client setup

For each hub, there needs to be a:

### Hub directory

A directory is created under the path defined by the `nfs.pv.baseShareName` cluster config.
Usually, this is:

1. `/homes` - for hubs that have in-cluster NFS storage

   Created using the infrastructure described in the [terraform section](topic:terraform).

2. `/export/home-01/homes` - for hubs that have the NFS server deployed manually

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

Parts of the *home* volume are mounted in different places for the users:
   * [user home directories](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L100)

     Z2jh will mount into `/home/jovyan` (the mount path) the contents of the path `<hub-directory-path>/<hub-name>/<username>` on the NFS storage server. Note that `<username>` is specified as a `subPath` - the *subdirectory* **in the volume to mount** at that given location.

   * shared directories
        * [/home/jovyan/shared](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L106-L109)

          Mounted for **all users**, showing the contents of `<hub-directory-path>/<hub-name>/_shared`. This mount is **readOnly** and users **can't** write to it.

        * [/home/jovyan/shared-readwrite](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L84-L86)

          Mounted **just for admins**, showing the contents of `<hub-directory-path>/<hub-name>/_shared`. This volumeMount is **NOT readonly**, so admins can write to it.

          ```{note}
          This feature comes from the [custom KubeSpawner](https://github.com/2i2c-org/infrastructure/tree/HEAD/helm-charts/basehub/values.yaml#L182) that the our community hubs use, that allows providing extra configuration for admin users only.
          ```
        *  the `allusers` directory - optional

           Can be mounted **just for admins**, showing the contents of `<hub-directory-path>/<hub-name>/`. This volumeMount is **NOT readonly**, so admins can write to it. It's purpose is to give access to the hub admins to all the users home directory to read and modify.

           ```yaml
            jupyterhub:
              custom:
                singleuserAdmin:
                  extraVolumeMounts:
                    - name: home
                      mountPath: /home/jovyan/allusers
            ```
