# Pre-pull a content repository

`nbgitpuller` is often recommended as the approach for pre-populating a user's file-system with a particular Git repository. However, in cases where the source repository is known a priori to be fixed for all users, we can use Kubernetes init containers to pre-provision the file-system with the contents of this repository on startup.

The benefits of using an init container to perform this operation are:

1. Failures in loading or merging of the Git repository do not stop users from accessing their servers
2. Alternative launch methods to `nbgitpuller` URLs now provision the file system with the necessary content.

The [jupyterhub-gitpuller-init] image is an example of an init container that fulfils this purpose. It requires a volume to be mounted onto `/home/jovyan`, and the necesasry inputs to be defined:

`TARGET_PATH`
: Destination to clone Git repository.

`SOURCE_REPO`
: URL of the Git repository to clone.

`SOURCE_BRANCH`
: Branch of the Git repository to clone.

## Defining the init container

The following configuration for the `jupyterhub-gitpuller-init` init container can be added to the `jupyterhub.singleuser` configuration for a particular cluster:

```yaml
jupyterhub:
  singleuser:
    initContainers:
      - name: jupyterhub-gitpuller-init
        image: public.ecr.aws/nasa-veda/jupyterhub-gitpuller-init:97eb45f9d23b128aff810e45911857d5cffd05c2
        env:
          - name: TARGET_PATH
            value: <YOUR_CLONE_PATH>
          - name: SOURCE_REPO
            value: <YOUR_GIT_REPO>
          - name: SOURCE_BRANCH
            value: <YOUR_GIT_BRANCH>
        volumeMounts:
          - name: home
            mountPath: /home/jovyan
            subPath: "{escaped_username}"
        securityContext:
          runAsUser: 1000
          runAsGroup: 1000
```

This init container will run for _all user profiles_.

[jupyterhub-gitpuller-init]: https://github.com/NASA-IMPACT/jupyterhub-gitpuller-init
