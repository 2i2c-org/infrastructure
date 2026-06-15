(pre-pull-user-images)=
# Pre-pull user images at node startup

Image pre-pulling before user arrival is not a feature enabled by default on the hubs, as it comes with an increase in cloud costs. However, there are cases when users need faster startup times like exams, events, or even just a hub with large images. In this situations, given that communities understand the cost tradeoff, this feature can be enabled.

More about it at https://z2jh.jupyter.org/en/stable/administrator/optimization.html#pulling-images-before-users-arrive

## Enable `continuous-image-puller`

The following config will pre-pull all explicitly specified images either through profiles or directly, on all nodes  when they start up.

```yaml
jupyterhub:
  prePuller:
    continuous:
      enabled: true
```

## Explicitly specify extra images to pre-pull

You can also specify additional images to pre-pull on the nodes. This can be either images used by init containers or extra containers.

Example:

```yaml
jupyterhub:
  prePuller:
    continuous:
      enabled: true
      extraImages:
        nbgitpuller:
          name: public.ecr.aws/nasa-veda/jupyterhub-gitpuller-init
          tag: 97eb45f9d23b128aff810e45911857d5cffd05c2
        s3fs:
          name: mas.dit.maap-project.org/root/che-sidecar-s3fs
          tag: 2i2c # This is a mutable tag, so may trigger re-pulls
```