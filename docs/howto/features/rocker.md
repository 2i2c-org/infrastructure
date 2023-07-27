# Use Rocker based R images

The [Rocker](https://rocker-project.org/) project is a community led set of
containers for use in the R ecosystem, similar to the [jupyter/docker-stacks](https://jupyter-docker-stacks.readthedocs.io/en/latest/)
images for the python ecosystem. They contain hand-picked useful libraries
determined by the R Community, along with a working RStudio setup. We should
treat them as meaningful upstream for users who want an environment that is
primarily R and RStudio.

## Why?

Why use the Rocker images when [jupyter/r-notebook](https://hub.docker.com/r/jupyter/r-notebook)
exists? A few reasons!

1. r-notebook does not have RStudio, and R users primarily use RStudio. It
   is very important for us, from the *JupyterHub* community, to respect this
   choice and support that to the extent possible with JupyterHub, rather than
   try to get them to move to Jupyter notebooks. Being able to use RStudio as
   well as Jupyter Notebooks is one of JupyterHub's great selling points, and
   we should capitalize!

2. r-notebook installs R packages from `conda`, while Rocker uses the
   [Posit Package Manager](https://packagemanager.posit.co/) CRAN snapshot.
   Both these provide binary packages, but the latter is *multiple orders of
   magnitude more popular* in the R ecosystem. Most R users install packages
   via `install.packages` or `devtools`, and those all work from CRAN with
   Posit Package Manager, not `conda`. So for an R native experience, we should
   continue to use Posit Package Manager's CRAN archive.

3. The [Rocker team](https://rocker-project.org/#team) is well respected within
   the R community, and they pick the base set of libraries to go into these
   images. This lets us provide a 'batteries included' experience to our end
   users with minimal need to inherit images.

## Picking the image to use

If we want to use the upstream image directly,
[rocker/binder](https://rocker-project.org/images/versioned/binder.html)
is the appropriate image to use, as it has JupyterHub,
[jupyter-rsession-proxy](https://github.com/jupyterhub/jupyter-rsession-proxy),
and whatever else is needed to work on a JupyterHub. It inherits from
[rocker/geospatial](https://rocker-project.org/images/versioned/rstudio.html),
which contains:

- [tidyverse](https://www.tidyverse.org/) set of packages
- A working LaTeX installation, set up to be usable with R's publishing infrastructure
- Geospatial packages

The version tags used refer to R versions only, and the [upstream repo](https://github.com/rocker-org/rocker-versioned2)
is only tagged for each new R version.

## Hub configuration

### Default user and home directory

The rocker project uses `rstudio` as the default user, with uid `1000`, for
non-root access. This is slightly different from repo2docker or the jupyter/docker-stacks
or pangeo-stacks images, which use the `jovyan` user with uid `1000`. This
is mostly fine in most people's cases, but because we explicitly set the
user home directory to `/home/jovyan` in `basehub/values.yaml`, we will
need to explicitly set user's home directory to `/home/rstudio` for rocker
based images. There isn't a problem with folks mixing rocker and other images
in the same home directory though, as the uid is the same. While this name
difference *does* cause some extra config to be required, we should stick to
it as part of respecting the other community's norms.

### Default URL to open

Mostly, we would want the hub to put users directly into RStudio after they
log in. Thanks to the [jupyter-rsession-proxy](https://github.com/jupyterhub/jupyter-rsession-proxy),
this just requires us to set `singleuser.defaultUrl` or `Spawner.default_url`
traitlet config.

## Configuration without `profileList`

When not using profileLists, the hub can be configured like this:

```yaml
jupyterhub:
  hub:
    config:
      KubeSpawner:
        # Ensures container working dir is homedir
        # https://github.com/2i2c-org/infrastructure/issues/2559
        working_dir: /home/rstudio
        # Launch into RStudio after the user logs in
        default_url: /rstudio
```

## Configuration with `profileList`

When using profileLists, it should probably look like this:


```yaml
jupyterhub:
  singleuser:
    profileList:
    - display_name: "Some Profile Name"
      profile_options:
        image:
          display_name: Image
          choices:
            geospatial:
              display_name: Rocker Geospatial
              default: true
              slug: geospatial
              kubespawner_override:
                image: rocker/binder:4.3
                # Launch into RStudio after the user logs in
                default_url: /rstudio
                # Ensures container working dir is homedir
                # https://github.com/2i2c-org/infrastructure/issues/2559
                working_dir: /home/rstudio
                # Because this is a list, it will override our default volume mounts
                volume_mounts:
                  # Mount the user home directory
                  - name: home
                    mountPath: /home/rstudio
                    subPath: "{username}"
                  # Mount the shared readonly directory
                  - name: home
                    mountPath: /home/rstudio/shared
                    subPath: _shared
                    readOnly: true
            scipy:
              display_name: Jupyter SciPy Notebook
              slug: scipy
              kubespawner_override:
                image: jupyter/scipy-notebook:2023-06-26
```

## User installed packages

In R, users can install packages with `install.packages` or similar R commands. Rocker
is configured to automatically install packages from the [Posit Package Manager](https://packagemanager.posit.co/client/#/),
which provides fast binary package installs.

They are installed under `/usr/local`, and hence *cleared on server stop*. So installed
packages will *not* persist across user sessions. 

If users need to have persistent packages installed, we would need a custom image.
