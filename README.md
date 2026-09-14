# Infrastructure for deployments

This repository contains deployment infrastructure and documentation for a federation of JupyterHubs that 2i2c manages for various communities.

See [the infrastructure documentation](https://infrastructure.2i2c.org) for more information.

## Building the documentation

The documentation is built with [the MyST Document Engine](https://mystmd.org).
Configuration lives in `docs/myst.yml` and the table of contents in `docs/toc.yml`.

### Automatically with `nox`

The easiest way to build the documentation in this repository is to use [the `nox` automation tool](https://nox.thea.codes/), a tool for quickly building environments and running commands within them.
This ensures that your environment has all the dependencies needed to build the documentation.

To do so, follow these steps:

1. Install `nox`

   ```console
   $ pip install nox
   ```

2. Build the documentation:

   ```console
   $ nox -s docs
   ```

This should create a local environment in a `.nox` folder, build the documentation (as specified in the `noxfile.py` configuration), and the output will be in `docs/_build/html`.

To start a live server that updates when you change local files:

```console
$ nox -s docs:live
```

### Manually

If you wish to build the documentation yourself, install the Python dependencies (MyST installs its own Node.js), then run it from the `docs/` folder:

```bash
pip install -r docs/requirements.txt
cd docs
python -m helper_programs.hub_info_table  # generates the hub tables
myst start                                # or `myst build --html`
```

This is the same set of steps that Read the Docs runs (see `.readthedocs.yaml`).
