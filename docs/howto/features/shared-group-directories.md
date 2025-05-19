(features:shared-group-directories)=
# Enable Shared Group Directories

Shared group directories provide a mechanism for users belonging to specific groups to have access to a common storage area within their JupyterHub environment. This guide outlines the steps to configure and enable this feature for a hub.

## Configuration Steps

Enabling shared group directories involves modifications in the hub's `values.yaml` file, specifically within the `jupyterhub.singleuser` and `jupyterhub.hub.extraConfig` sections.

### 1. Ensure Correct Volume Ownership and Permissions

It's crucial that the shared group directories have the correct ownership and permissions so that user pods can read and write to them. We already have an `initContainer` defined for fixing volume ownership. Look for a section similar to this in the hub's `values.yaml` under `jupyterhub.singleuser.initContainers`, add a `volumeMount` for `/home/jovyan/shared-group` that points to the underlying shared storage (e.g., `subPath: _shared-group`) and ensure it includes the necessary `chown` commands for the shared directories:

```yaml
# Example from config/clusters/maap/staging.values.yaml
jupyterhub:
  singleuser:
    initContainers:
      - &volume_ownership_fix_initcontainer
        name: volume-mount-ownership-fix
        image: busybox:1.36.1
        command:
          - sh
          - -c
          - >
            id &&
            chown 1000:1000 /home/jovyan /home/jovyan/shared /home/jovyan/shared-public /home/jovyan/shared-group &&
            if [ -d "/home/jovyan/shared-group" ] && [ "$(ls -A /home/jovyan/shared-group)" ]; then
              chown 1000:1000 /home/jovyan/shared-group/* || true;
            fi &&
            ls -lhd /home/jovyan
        securityContext:
          runAsUser: 0 # Run as root to change ownership
        volumeMounts:
          - name: home
            mountPath: /home/jovyan
            subPath: "{escaped_username}"
          # Mounted without readonly attribute here,
          # so we can chown it appropriately
          - name: home
            mountPath: /home/jovyan/shared
            subPath: _shared
          - name: home
            mountPath: /home/jovyan/shared-public
            subPath: _shared-public
          # _shared-group is the directory that contains the shared directories for each group
          # We mount it here to ensure that the initContainer has access to it and can set the ownership
          # correctly.
          - name: home
            mountPath: /home/jovyan/shared-group
            subPath: _shared-group
```

### 2. Configure Group-Specific Volume Mounts via `extraConfig`

The core logic for mounting specific shared directories based on user group membership is handled by `c.KubeSpawner.group_overrides` within `jupyterhub.hub.extraConfig`.

First, we need to ensure that the `volume_mounts` and `volumes` are defined as dictionaries, not lists. This allows us to add new entries without replacing the entire list. This is done in the `00-volumes-and-volume-mounts-as-dict` entry in the `extraConfig` section below.
(This step is not necessary if `volume_mounts` and `volumes` are already converted to dictionaries in basehub config)

Then, we define the group-specific volume mounts in the `01-group-shared-directories` entry. This configuration allows us to specify which groups have access to which shared directories:

```yaml
  # In jupyterhub.hub.extraConfig:
  # Example from config/clusters/maap/staging.values.yaml
  extraConfig:
    00-volumes-and-volume-mounts-as-dict: |
      # The base jupyterhub config in zero-to-jupyterhub defines
      # volumes and volume_mounts as lists.
      # But we can't add new volumes or volume_mounts to the list
      # as that replaces the entire list.
      # So we convert them to dictionaries, which allows us to
      # add new volumes and volume_mounts as needed.
      if isinstance(c.KubeSpawner.volumes, list):
        existing_volumes = c.KubeSpawner.volumes
        c.KubeSpawner.volumes = {}
        for volume in existing_volumes:
          c.KubeSpawner.volumes[volume["name"]] = volume
      if isinstance(c.KubeSpawner.volume_mounts, list):
        existing_volume_mounts = c.KubeSpawner.volume_mounts
        c.KubeSpawner.volume_mounts = {}
        for idx, volume_mount in enumerate(existing_volume_mounts):
          c.KubeSpawner.volume_mounts[f"{idx}-{volume_mount['name']}"] = volume_mount
    01-group-shared-directories: |
      c.KubeSpawner.group_overrides = {
        "00-group-CPU-L-extra-volume-mounts": {
          "groups": ["CPU:L"], # The group name defined in Keycloak
          "spawner_override": {
            "volume_mounts": {
              "00-group-CPU-L-shared-dir": { # The shared directory the group has access to
                "name": "home",
                "mountPath": "/home/jovyan/shared-group/CPU_L",
                "subPath": "_shared-group/CPU_L",
                "readOnly": False
              },
            }
          },
        },
        "01-group-GPU-T4-extra-volume-mounts": {
          "groups": ["GPU:T4"],
          "spawner_override": {
            "volume_mounts": {
              "00-group-GPU-T4-shared-dir": {
                "name": "home",
                "mountPath": "/home/jovyan/shared-group/GPU_T4",
                "subPath": "_shared-group/GPU_T4",
                "readOnly": False
              },
            }
          },
        }
      }
```


