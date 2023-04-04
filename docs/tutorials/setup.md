(tutorials:setup)=
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

On other operating systems, the documentation links above should help you find
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
All these providers provide decent command line tools that we need to have locally
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

### Terraform

We use [terraform](https://www.terraform.io/) to manage our infrastructure in the cloud.
So in order to update existing clusters or add new ones, you'll need to install this tool.

On a Mac, you can easily [install it](https://learn.hashicorp.com/tutorials/terraform/install-cli#install-terraform) with `homebrew`:

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

Checkout this [information about terraform](topic:terraform) for how to configure and use it.

## Step 2: Setup the python environment

Our deployment scripts are all written in python, so you'll need to have a recent
version of Python 3 installed. There are innumerable ways to install python on your
system, so we will not go into them here. Two quick suggestions are to either use
[miniforge](https://github.com/conda-forge/miniforge) if you are already familiar with
`conda`, or use `brew install python3` on a Mac.

Once Python is installed, you need to create a virtual environment to install the specific
libraries we will use. Again this depends on how you installed python, and whether you
want to use `conda` or `pip`.

Once you have a virtual environment setup and activated, install the libraries
required with `pip install -r requirements.txt -r dev-requirements.txt -e .`

Now you are all ready to use our deployer scripts! Note if dependencies get
added you will to run the installation again.

Remember you need to *activate the environment* you installed these libraries into each
time you use any of our scripts.

## Step 3: Setup the git pre-commit hooks

Install pre-commit [pre-commit installation instruction](https://pre-commit.com/#introduction)

In the root of the checked out `infrastructure` repo run the below to install
the local pre-commit hooks.

```
pre-commit install --install-hooks
``` 

## Step 4: Authenticate with Google Cloud to decrypt our secret files

Permission to decrypt the secret files in this repo is managed via
Google Cloud's [Key Management Service](https://cloud.google.com/security-key-management),
**regardless of the cloud provider running the cluster you are interested in**.
So to decrypt our secrets, you *must* authenticatie to google cloud via `gcloud`.

You need to already have permissions to the `two-eye-two-see` project via
your `2i2c.org` Google Account. If you don't have this, please ask a team member.

1. Run `gcloud auth login`, and when the browser window pops up, login with
   your `2i2c.org` google account.
2. Run `gcloud auth application-default login` and repeat the process again.

Tada, now you're logged in!

## Step 5: Access kubernetes clusters with the `deployer` module

```{note}
You should have already been given access to the `two-eye-two-see` Google Cloud
Project as part of onboarding. If not, you might get errors from `sops` about missing permissions
during this step. Please chat with whoever onboarded you to make sure you have the
required cloud access.
```

Our deployer has a convenient way to authenticate you in order
to interact with a kubernetes cluster from the commandline - the `use-cluster-credentials`
subcommand.

1. Look for the cluster you want to access - there is one cluster per directory inside
   `config/clusters`.
2. Run `deployer use-cluster-credentials CLUSTER_NAME` from the terminal, and this will authenticate you
   to the correct kubernetes cluster!

Test that you've been correctly authenticated by running `kubectl get node`, which should list the nodes in the
kubernetes cluster selected.

The `use-cluster-credentials` subcommand actually creates a new shell and sets environment variables to allow access to the chosen cluster, so make sure to run `exit` or `Ctrl`+`D`/`Cmd`+`D` when you are finished.
