# Manage a hub's user environment

(customize/custom-image)=
## Use a custom user image

Community hubs use an image we curate as the default. This can be replaced with your
own custom image fairly easily. However, custom images should be maintained
by the hub admins, and we won't be able to help much with things in it.

### Image requirements

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

### Which image registry to use?

While you can push your image to [dockerhub](https://hub.docker.com), it now has
pretty [strict usage limits](https://www.docker.com/increase-rate-limits). This
could cause disruptions in your hub if a new image can not be pulled due to
these rate limits. We recommend the following image repositories:

1. [quay.io](https://quay.io/). Owned by RedHat / IBM. Easiest to get started in,
   and **recommended as the default**
2. [Google Artifact Registry](https://cloud.google.com/artifact-registry), if
   you already have infrastructure running on Google Cloud.
3. [AWS Elastic Container Registry](https://aws.amazon.com/blogs/aws/amazon-ecr-public-a-new-public-container-registry/)
   if you already have infrastructure running on AWS.
4. [GitHub container registry](https://docs.github.com/en/free-pro-team@latest/packages/guides/about-github-container-registry).
   It integrates better with GitHub, but doesn't have a clear policy on rate limits
   yet.

### Configuring your hub to use the custom image

We define arbitrary [`zero to jupyterhub on kubernetes`](https://zero-to-jupyterhub.readthedocs.io/en/stable/resources/reference.html) values in `config/clusters/CLUSTER_NAME/HUB_NAME.values.yaml` files, which we can use to set the image name and tag.
Here are some example values with only the useful bits.

```yaml
jupyterhub:
  singleuser:
    image:
      name: pangeo/pangeo-notebook
      tag: "2020.12.08"
```

This can be any image name & tag available in a public container registry.

Whenever you push a new image, you should make a PR that updates the tag here.
Only on merge will the hub get the new image.

Another way to update the image is to use the [configurator](https://docs.2i2c.org/en/latest/admin/howto/configurator.html).

### Split up an image for use with the repo2docker-action

Sometimes we have user images defined in a repo, and we want to extract
it to a standalone repo so it can be used with the [repo2docker action](https://github.com/jupyterhub/repo2docker-action).
But we want to retain full history of the image still, so we can look
back and see why things are the way they are, as well as credit the people
who contributed over time. This page documents the git-fu required to
make this happen.

1. Clone the base repository you are extracting the image from.
   We will be performing destructive operations on this clone,
   so it has to be a fresh clone.

    ```bash
    git clone <base-repo-url> <hub-image> --origin source
    ```

    We name the directory `<hub-image>` as that would be the name of the
    repo with just the user image. We ask git to name the remote it creates be
    called `source`, as we will create a new GitHub repo later that will be `origin`.

2. Make sure [git-filter-repo](https://github.com/newren/git-filter-repo)
   is installed. It should be available in [brew or other package managers](https://github.com/newren/git-filter-repo/blob/main/INSTALL.md)

3. Run `git-filter-repo` to remove everything from the repo except the
   image directory.

   ```bash
    git filter-repo --subdirectory-filter <path-to-image-directory> --force
    ```

    The repo root directory now contains the contents of `<path-to-image-directory>`,
    as well as full git history for any commits that touched it! This way,
    we do not lose history or attribution.

4. Create a user image repository in GitHub based off [this template](https://github.com/2i2c-org/hub-user-image-template).
   The template makes it much easier to setup repo2docker-action on it.

5. Add the new user image repo as a remote you can push commits to / pull commits from.
   This will be the primary location of this repo now, so let's call it `origin`.

   ```bash
   git remote add origin git@github.com:<your-org-or-user-name>/<your-repo-name>.git
   ```

6. Fetch the new repo and check out the `main` branch, as that is the final
   destination for our image contents.

   ```bash
    git fetch origin
    git checkout main
    ```

7. Remove the `environment.yml` file from the repo - it is present as an example
   only, and we have our own we are bringing.

   ```bash
   git rm environment.yml
   git commit -m 'Remove unused environment.yml file'
   ```

8. Merge the branch we prepared earlier with just our image contents into this
   `main` branch, while telling git to not freak out about them being from different
   repos initially.

   ```bash
   git merge staging --allow-unrelated-histories  -m 'Bringing in image directory from deployment repo'
   git push origin main
   ```

   In this case, `staging` was the name of the branch in the source
   repo, and `main` is the name of the main branch in the new user image
   repo.

9. Now follow the instructions in the README of your new repo to complete setting up
   the repo2docker action as well as using this on your hub!
