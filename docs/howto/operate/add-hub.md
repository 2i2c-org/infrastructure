# Add a new hub

## Step 1: Decide where the hub will live

Hubs need to exist on a kubernetes cluster, so we will need to
decide which cluster it should live in.

1. For standalone hubs where we are being paid or the client has cloud
   credits, we will need to create a cluster specifically for this hub
   before deploying it.
2. For hubs we are running for free, they will go into the `pilot-hubs`
   cluster.
3. Hubs run with the support of [cloudbank](https://www.cloudbank.org/),
   will go in the `cloudbank` cluster.

Each cluster has configuration + list of hubs it supports under
`config/hubs/<cluster-name>.cluster.yaml`.

## Step 2: Decide the template used for the hub

Based on the kinda usage expected of the hub select a [hub template](../../topic/hub-templates.md)
to be used.

## Step 4: Decide the authentication provider to be used

In consultation with the users, decide
[which authentication provider](https://pilot.2i2c.org/en/latest/admin/configuration/login.html#authentication)
the hub should use. While this can be changed later, it's a messy
process - so we should try to get this right the first time.

## Step 5: Decide the user image for the hub

The default user image is present in this repository (`images/user`),
and is geared towards simple datascience classes - with both R and
Python. Determine if this is acceptable - if not, you need to
make a [custom image](../configure/update-env.md) for them.

## Step 6: Add hub config

Add an entry for the hub in `config/hubs/<cluster-name>.cluster.yaml` for this hub.
The following docs might be helpful:

1. [Configuration Structure](../../topic/config.md)
2. [JSON Schema for `.cluster.yaml` file](https://github.com/2i2c-org/pilot-hubs/blob/master/config/hubs/schema.yaml)
3. [Zero to JupyterHub on k8s Docs](https://zero-to-jupyterhub.readthedocs.io/en/latest/), since ultimately
   that is what we are configuring.

## Step 7: Deploy manually and test

[Deploy the hub manually](./manual-deploy.md) and test to make sure it works
the way you would like it to. This might take some iteration and multiple
tries. Specifically test that at least the following work ok:

1. Authentication provider
2. Admin user access
3. User image in use
4. Default user interface when the user logs in (lab, notebook, rstudio, retrolab, etc)
5. Home page display configuration
6. (Optionally) `dask-gateway` functionality
7. (Optionally) Access to any cloud resources (like storage buckets, etc)
   granted to the hub users
## Step 8: Make a PR

Make a PR with your changes, referencing the issue for creation of the hub. Seek
review from someone else, and get this merged!

Getting this merged will mark the hub as being deployed.