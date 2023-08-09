# Infrastructure for deployments

This repository contains deployment infrastucture and documentation for a federation of JupyterHubs that 2i2c manages for various communities.

See [the infrastructure documentation](https://infrastructure.2i2c.org) for more information.

## Building the documentation

The documentation is built with [the Sphinx documentation engine](https://sphinx-doc.org).

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

This should create a local environment in a `.nox` folder, build the documentation (as specified in the `noxfile.py` configuration), and the output will be in `docs/_build/dirhtml`.

To build live documentation that updates when you update local files, run the following command:

```console
$ nox -s docs -- live
```

### Manually with `conda`

If you wish to manually build the documentation, you can use `conda` to do so.

1. Create a `conda` environment to build the documentation.

   ```bash
   conda env create -f docs/environment.yml -n infrastructure-docs
   ```

2. Activate the new environment:

   ```bash
   conda activate infrastructure-docs
   ```

3. Build the documentation:

   ```bash
   make html
   ```

This will generate the HTML for the documentation in the `docs/_build/dirhtml` folder.
You may preview the documentation by opening any of the `.html` files inside.

### Build the documentation with a live server

You can optionally build the documentation with a **live server** to automatically preview the changes as you build the docs. To use this, run `make live` instead of `make html`.

### Check for broken links

You can check for broken links in our documentation with the [Sphinx linkcheck builder](https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder).
This will build the documentation and test every link to make sure that it resolves properly.
We use a GitHub Action to check this in our CI/CD, so this generally shouldn't be needed unless you want to manually test something.
To check our documentation for broken links, run the following command from the `docs/` folder:

```bash
make linkcheck
```

This will build the documentation, reporting broken links as it goes.
It will output a summary of all links in a file at `docs/_build/linkcheck/output.txt`.
