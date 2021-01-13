# Using a custom image

Pilot hubs use an image we curate as the default. This can be replaced with your
own custom image fairly easily. However, custom images should be maintained
by the hub admins, and we won't be able to help much with things in it.

## Image requirements

On top of whatever you are using, your image should match the following requirements:

1. The `jupyterhub` package is installed in such a way that the command `jupyterhub-singleuser`
   works when executed with the image. 99% of the time, this just means you need to
   install the `jupyterhub` python package.

2. Everything should be able to run as a non-root user, most likely with a uid 1000. 

There are a few options to help make this easier.

1. Use [repo2docker](https://repo2docker.readthedocs.io) to build your image. 
2. Use a [pangeo curated docker image](https://github.com/pangeo-data/pangeo-docker-images/).
   They have an 'onbuild' variant of their images that lets you easily customize
   them.
3. Use a [jupyter curated docker image](https://jupyter-docker-stacks.readthedocs.io/en/latest/).

Nothing will be installed on top of this by us, so you really have full control of what
goes in your environment.

## Which image registry to use?

While you can push your image to [dockerhub](https://hub.docker.com), it now has
pretty [strict usage limits](https://www.docker.com/increase-rate-limits). This
could cause disruptions in your hub if a new image can not be pulled due to
these rate limits. We recommend the following image repositories:

1. [quay.io](https://quay.io/). Owned by RedHat / IBM. Easiest to get started in,
   and **recommended as the default**
2. [Google Artifact Registry](https://cloud.google.com/artifact-registry), if
   you already have infrastructure running on Google Cloud.
3. [AWS Public Container Registry](https://aws.amazon.com/blogs/aws/amazon-ecr-public-a-new-public-container-registry/)
   if you already have infrastructure running on AWS.
4. [GitHub container registry](https://docs.github.com/en/free-pro-team@latest/packages/guides/about-github-container-registry).
   It integrates better with GitHub, but doesn't have a clear policy on rate limits
   yet.

## Configuring your hub to use the custom image

`hubs.yaml` can contain arbitry `zero to jupyterhub on kubernetes` config, so we
can use that to set the image name & tag. Here is some example config, with only
the useful bits.

```yaml
- name: custom-image-hub
  ...
  config:
    base-hub:
      jupyterhub:
        singleuser:
          image:
            name: pangeo/pangeo-notebook
            tag: 2020.12.08
```

This can be any image name & tag. 

Whenever you push a new image, you'll have to make a PR that updates the tag here.
Only on merge will the hub get the new image.
