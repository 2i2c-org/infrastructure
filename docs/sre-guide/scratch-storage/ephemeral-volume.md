(sre-guide:scratch-storage-ephem)=
# Setting up scratch storage with ephemeral volumes

This guide covers how to setup a scratch storage in `/tmp` using an `ephemeral` volume.

## Add a scratch profile option

We can provide users with access to scratch storage by adding a `scratch_disk` profile option entry in the `singleuser.profileList` configuration. Here, we'll define possible `/tmp` choices, such as a larger `/tmp` disk and/or _faster_ disks for high-performance workloads. We can combine node-level scratch (see @sre-guide:scratch-storage-node) with dedicated scratch storage using profile options:
```yaml
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
              description: Max of 200GB
              default: true
              kubespawner_override:
                # ...
            # This option will define a dedicated ephemeral volume
            02_gb_500:
              display_name: Dedicated 500GB
              description: 500GB dedicated to just you
              kubespawner_override:
                # ...
```
When defining the dedicated ephemeral volume `kubespawner_override`, we need to specify special `storageClassName` and `volumeAttributesClassName` attributes that allow the CSI driver to provision the correct kind of temporary volume.

## Define the volume attributes and storage class

:::::{tab-set}
::::{tab-item} AWS
:sync: aws-key

On AWS, the default storage class is named `ebs-csi-default-sc`. This will typically represent a `gp3` volume. Meanwhile, the `VolumeAttributesClass` is managed by the support Helm chart, and is named `scratch-disk`. In `kubespawner_override`, we'll define a temporary ephemeral volume that includes this configuration.

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
              description: Max of 200GB
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
                            type: temporary-user-scratch
                        spec:
                          accessModes: [ReadWriteOnce]
                          storageClassName: ebs-csi-default-sc  # Set this & volumeAttributes explicitly
                          volumeAttributesClassName: scratch-disk
                          resources:
                            requests:
                              storage: 500Gi
```

We may wish to increase the performance of the ephemeral disk. To do this, we'll modify the support chart values for the `scratch-disk` `VolumeAttributesClass`:
```{code-block} yaml
:filename: support.values.yaml

scratchDiskVAC:
  parameters:
    provisioned-iops: "3000"
    provisioned-throughput: "50"

```
See [the Kubernetes documentation](https://kubernetes.io/docs/concepts/storage/volume-attributes-classes/#the-volumeattributesclass-api) for more details on these parameters.

::::

:::::

