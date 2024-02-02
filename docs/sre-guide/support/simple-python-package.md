# Add a simple python package to an image we maintain

This runbook describes the steps folks can take when they receive a request for
adding a python package to an image we maintain for a community. Most requests are for
a simple, uncomplicated package addition. This guide helps you determine if the request
is simple, and if so, complete it.

## Pre-requisites

1. We (2i2c) are responsible for maintaining this image. There is currently no single source of
   truth for determining this, unfortunately - please ask in the `#partnerships` channel if you
   are not sure.

   ```{Note}
   If we do not maintain the image for a community, we should have a template response to be
   sent back here.
   ```

2. The image is maintained on a GitHub repo we have full rights on.

3. The image is built and pushed with [repo2docker-action](https://github.com/jupyterhub/repo2docker-action)

4. The request is for a python package.

5. The image is constructed in one of the following ways:
    a. It is using repo2docker files, and has an `environment.yml` file
    b. It is inheriting from one of the following community maintained upstream images via a `Dockerfile`.
        i. [jupyter/docker-stacks](https://github.com/jupyter/docker-stacks)
        ii. [pangeo-docker-images](https://github.com/pangeo-data/pangeo-docker-images/)

If *any* of these pre-requisites are not met, go straight to [escalation](sre-guide:support:simple-python-package:escalation).

## Determine if this is a 'simple' package addition

### Q1: Is the python package being requested available on `pip` or the `conda-forge` channel?

- [conda-forge search](https://anaconda.org/search). Verify that the package is in the `conda-forge` channel here, rather than in any other channel.
- [pypi search](https://pypi.org/)

#### No

- The package is from GitHub -> Tell the requester to release it on PyPI, and we
  can install it from there. In the meantime, they can test it within their
  environment by just `pip install`ing from their github repo.

- Package is available in a non-conda-forge channel ->
  [Escalate](sre-guide:support:simple-python-package:escalation) to rest of the
  team, as mixing conda channels can get messy and complex.

#### Yes

Go to Q2.

### Q2: Is this package part of the ML ecosystem?

There are two distinct ML ecosystems in python - based on
[tensorflow](https://www.tensorflow.org/) and [pytorch](https://pytorch.org/).
Does the package depend transitively on either of these packages?

#### Check dependencies on `pip`

If we are installing from `PyPI` via `pip`, you can check transitive dependencies
via the excellent [libraries.io](https://libraries.io).

1. Go to the [libraries.io/pypi](https://libraries.io/pypi/) page - this collects
   and provides many useful pieces of information about packages on PyPI.
2. Search for the name of the package, and open its page.
3. In the right sidebar, under 'Dependencies', click 'Explore' dependencies.
   This should take you to a dependency tree page, showing all dependencies
   (including transitive dependencies). Here is what that looks
   like for [pymc3](https://libraries.io/pypi/pymc3/3.11.5/tree).
4. Search for `tensorflow` or `torch` (the package name for pytorch) here.

#### Check dependencies on `conda`

If the package is in `conda-forge` and you have [mamba](https://mamba.readthedocs.io)
locally installed, you can use the [mamba repoquery](https://mamba.readthedocs.io/en/latest/user_guide/mamba.html#repoquery)
command. For example, to find all the dependencies of `pymc`, you would run:

```bash
mamba repoquery depends -c conda-forge pymc --tree
```

This should show you all the transitive dependencies

#### No

Yes, this is a *simple* package addition. Proceed to implementation.

#### Yes

Go to Q3

### Q3: Is the base package (tensorflow or pytorch) already installed in the image?

#### Yes

Yes, this is a *simple* package addition. Proceed to implementation.

#### No

No, this is not a simple package addition.
[Escalate](sre-guide:support:simple-python-package:escalation) to the rest of
the team, to help choose between:

1. Adding ML packages to existing image
2. Suggesting the community to use a different image as part of a `profileList`
3. Suggesting a new hub be deployed for ML use cases

## Implementing a simple package addition

### Guidelines for choosing conda-forge vs pypi

1. If the package is ML related, and the base package (tensorflow or pytorch) is
   already present in the image, use the same installation method (conda-forge or
   PyPI) that the base package uses. This reduces intermixing of dependencies,
   which may cause breakage.
2. If the package is present on conda-forge, prefer that over PyPI

*If* there is an `environment.yml` file present, add the package there. If
*getting from `conda-forge`, it goes under the `dependencies`. If we are getting
*this from `PyPI`, it goes under the `pip` section under `dependencies`.

### Determine the latest version & pin to latest minor version.

**Ideally**, we will use a lock file for each image we maintain to have perfect
*pinning. However, we currently do not have that. Until then, we should use pin
*to the latest minor version of the requested package. So if the latest version
*is `2.0.5`, we can specify `==2.0.*` as the version constraint. While this
*still allows for versions of *dependent* packages to drift during rebuilds, it
*at least pins the *directly requested package* to an acceptable level (compared
*to not specifying a version at all).

You can find the current latest version from either PyPI or `conda-forge` (depending
on where it is being installed from, per the previous step).

### Provenance

Add a comment linking back to the support ticket where this package was requested.

### Does the build succeed?

We use [repo2docker-action](https://github.com/jupyterhub/repo2docker-action) to build and test PRs made to image repos. If the package can be successfully resolved and installed given our version constraints, the PR will have a successful build.

#### Yes

You can self merge the PR and roll it out to staging for the requester to test. The following response template may be used:

> Hello {{ name of requester }}
>
> We have installed the package you requested via {{ link to PR }}, and I have rolled it out to the staging hub at {{ link to staging hub }}. Can you test it out and let me know if it looks good? If so, I can roll it out to production.
>
> Thanks!

#### No

[Escalate](sre-guide:support:simple-python-package:escalation) to the whole team
so this can be debugged. We should communicate this escalation to the requester as well.
The following template may be used:

> Hello {{ name of requester }}
>
> We tried to add the package you requested in {{ link to PR }}. However, it looks like the package addition is not simple, and the build has failed. I've escalated this to our general engineering prioritization process, and we will get back to you once we have more information. Thank you for your patience!
>
> Thanks!

(sre-guide:support:simple-python-package:escalation)=
## Escalation

If this is *not* a simple package installation, escalate this to rest of engineering in the following way:

1. If it doesn't already exist, create a [freshdesk tracking issue](https://github.com/2i2c-org/infrastructure/issues/new?assignees=&labels=support&projects=&template=5_freshdesk-ticket.yml&title=%5BSupport%5D+%7B%7B+Ticket+name+%7D%7D)
   in the `2i2c-org/infrastructure` repository. Make sure to fill in whatever you have learnt so
   far.
2. Raise this in the `#support-freshdesk` channel on slack for further help and action.
