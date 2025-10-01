# The `deployer` module

## Summary

The `deployer` is a Python module that automates various tasks that 2i2c undertake to manage 2i2c-hosted JupyterHubs.

## Installing the deployer

The deployer is packaged as a local package (not published on PyPI). You can
use `pip` to install it.
You may wish to create a virtual environment using `venv` or `conda` first.

```bash
pip install --editable .
```

The `--editable` makes sure any changes you make to the deployer itself are
immediately effected.

## The directory structure of the deployer package

The deployer has the following directory structure:

```bash
├── README.md
├── __init__.py
├── __main__.py
├── cli_app.py
├── commands
├── health_check_tests
├── infra_components
├── keys
└── utils
```

### The `cli_app.py` file

The `cli_app.py` file is the file that contains the main `deployer` typer app and all of the main sub-apps "attached" to it, each corresponding to a `deployer` sub-command. These apps are used throughout the codebase.

### The `__main__.py` file

The `__main__.py` file is the main file that gets executed when the deployer is called.
If you are adding any sub-command functions, you **must** import them in this file for them to be picked up by the package.

### The `infra_components` directory

This is the directory where the files that define the `Hub` and `Cluster` classes are stored. These files are imported and used throughout the deployer's codebase to emulate these objects programmatically.

### The `utils` directory
This is where utility functions are stored. They are to be imported and used throughout the entire codebase of the deployer.


### The `commands` directory

This is the directory where all of the code related to the main `deployer` sub-commands is stored.

Each sub-commands's functions are stored:
- either in a single Python file where such thing was straight-forward
- or in a directory that matches the name of the sub-command, if it's more complex and requires additional helper files.

The `deployer.py` file is the main file, that contains all of the commands registered directly on the `deployer` main typer app, that could not or were not yet categorized in sub-commands.

### The `health_check_tests` directory

This directory contains the tests and assets used by them. It is called by `deployer run-hub-health-check` command to determine whether a hub should be marked as healthy or not.

## The deployer's main sub-commands
See https://infrastructure.2i2c.org//reference/cli/ for more details.

## Running Tests

To execute tests on the `deployer`, you will need to install the development requirements and then invoke `pytest` from the root of the repository.

```bash
$ pwd
[...]/infrastructure/deployer
$ cd .. && pwd
[...]/infrastructure
$ pip install -e .[dev]
$ python -m pytest -vvv
```
