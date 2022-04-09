# Setting up your local environment to work on this repo

This tutorial will guide you through all the steps needed to have a fully
functional local environment that can perform tasks on our clusters and hubs
using the tooling in this repo.

## Step 1: Install required tools

We'll need a bunch of different tools that are focused around interacting
with [kubernetes](https://kubernetes.io) and various cloud providers.

### Kubernetes access tools

We interact with kubernetes a *lot*, and these are the primary tools we use
to interact with them:

1. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
2. [helm](https://helm.sh/)

On a Mac, you can install these easily with `homebrew`:

```bash
brew install helm kubectl
```

On other operating systems, the documentation link above should help you find
ways of installing them.

### Secret decryption tools

The wonderful [sops](https://github.com/mozilla/sops/) tool is used to encrypt and
keep secrets *in* our repository.

On a Mac, you can install this easily with `homebrew`:

```bash
brew install sops
```

You can download releases for other platforms from [the sops github releases page](https://github.com/mozilla/sops/releases)

### Cloud provider tools

We primarily interact with Google Cloud, Amazon Web Services (AWS) and Azure.
All these providers provide decent commandline tools that we need to have locally
installed.

1. [gcloud](https://cloud.google.com/sdk)
2. [aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. [az](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

On a Mac, you can easily install them all with `homebrew`:

```bash
brew install google-cloud-sdk awscli azure-cli
```

For other platforms, consult the documentation in the links above to find
installation methods.

## Step 2: Setup the python environment

Our deployment scripts are all written in python, so you'll need to have a recent
version of Python 3 installed. There are innumerable ways to install python on your
system, so we will not go into them here. Two quick suggestions are to either use
[miniforge](https://github.com/conda-forge/miniforge) if you are already familiar with
`conda`, or use `brew install python3` on a Mac.

Once Python is installed, you need to create a virtual environment to install the specific
libraries we will use. Again this depends on how you installed python, and wether you
want to use `conda` or `pip`.

Once you have a virtual environment setup and activated, install the libraries
required with `pip install -r requirements.txt`. Now you are all ready to use our deployer
scripts!

Remember you need to *activate the environment* you installed these libraries into each
time you use any of our scripts.

## Step 2: Authentication with Google Cloud to help decrypt our secret files

Permission to decrypt the secret files in this repo is managed via
Google Cloud's [Key Management Service](https://cloud.google.com/security-key-management),
**regardless of the cloud provider running the cluster you are interested in**.
So authentication to google cloud via `gcloud` is *required*.

You need to already have permissions to the `two-eye-two-see` project via
your `2i2c.org` Google Account. If

1. Run `gcloud auth login`, and when the browser window pops up, login with
   your `2i2c.org` google account.
2. Run `gcloud auth application-default login` and repeat the process again.

Tada, now you're logged in!

## Step 3: Getting access to any of our kubernetes clusters with `deployer.py`

```{note}
You should have already been given access to the `two-eye-two-see` Google Cloud
Project as part of onboarding. If not, you might get errors from `sops` about missing permissions
during this step. Please chat with whoever onboarded you to make sure you have the
required cloud access.
```

Our deployer has a very convenient way to set up all the authentication necessary
for you to interact with a kubernetes cluster from the commandline - the `use-cluster-credentials`
subcommand.

1. Look for the cluster you want to try accessing - there is one cluster per directory inside
   `config/clusters`.
2. Run `python3 deployer use-cluster-credentials` from the terminal, and this will authenticate you
   to the correct kubernetes cluster!

You can test this out by running `kubectl get node`, which should list the nodes in the
kubernetes cluster selected.

