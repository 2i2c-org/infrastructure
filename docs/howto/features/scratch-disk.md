(howto:features:scratch-disk)=
# Setting up larger, dedicated `/tmp` for users

Because the hub home storage is based on NFS, it's only supposed to be used for
storing small data and code. Storing large datasets is not recommended because
it can get expensive and inefficient pretty quickly. Instead, we recommend using
cloud object storage combined with scratch storage that is local to the node
where the notebook server is running.


This guide covers how to setup a scratch storage in `/tmp` using an `ephemeral` volume.

## Add a scratch profile option

We can provide users with access to scratch storage by adding a `scratch_disk`
profile option entry in the `singleuser.profileList` configuration. Here, we'll
define possible `/tmp` choices, such as a larger `/tmp` disk and/or _faster_
disks for high-performance workloads.

Our hub values therefore must be modified as follows:
```{code-block} yaml
:filename: hub.values.yaml
:linenos:
:emphasize-lines: 37,38

singleuser:
  profileList:
    - display_name: Choose your environment and resources
      default: true
      profile_options:
        image:
          # ...
        scratch_disk:
          display_name: Scratch Disk on /tmp
          choices:
            # This option just uses the default node-level /tmp
            01_standard:
              display_name: Standard
              default: true
              kubespawner_override:
                # ...
            # This option will define a dedicated ephemeral volume
            02_gb_500:
              display_name: Dedicated 500GB
              description: 500GB dedicated to just you
              kubespawner_override:
                volume_mounts:
                  tmp:
                    name: big-tmp
                    mountPath: /tmp
                volumes:
                  big-tmp:
                    name: big-tmp
                    ephemeral:
                      volumeClaimTemplate:
                        metadata:
                          labels:
                            hub.jupyter.org/volume-purpose: user-scratch
                            hub.jupyter.org/username: '{username}'
                            hub.jupyter.org/servername: '{servername}'
                          annotations:
                            hub.jupyter.org/username: '{unescaped_username}'
                            hub.jupyter.org/servername: '{unescaped_servername}'
                        spec:
                          accessModes: [ReadWriteOnce]
                          storageClassName: <set-according-to-cloud-provider> # Set this & volumeAttributes explicitly
                          volumeAttributesClassName: scratch-disk
                          resources:
                            requests:
                              storage: 500Gi
```

You have to set the `storageClassName` explicitly. For AWS, it's `ebs-csi-default-sc` for `gp3` volumes, and
`dynamic-rwo` for GKE.

You can also restrict access to specific groups via [`allowed_groups`](howto:features:profile-restrict)

We may wish to increase the performance of the ephemeral disk. To do this, we'll modify the support chart values for the `scratch-disk` `VolumeAttributesClass`:
```{code-block} yaml
:filename: support.values.yaml

scratchDiskVAC:
  parameters:
    iops: "4000"
    throughput: "400"

```
See [the Kubernetes documentation](https://kubernetes.io/docs/concepts/storage/volume-attributes-classes/#the-volumeattributesclass-api) for more details on these parameters. Available parameters differ by cloud provider - see docs for ([AWS](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/parameters.md)), [GCP](https://github.com/kubernetes-sigs/gcp-compute-persistent-disk-csi-driver/blob/master/README.md#createvolume-parameters) and [Azure](https://github.com/kubernetes-sigs/azuredisk-csi-driver/blob/master/docs/driver-parameters.md).

::::

:::::

