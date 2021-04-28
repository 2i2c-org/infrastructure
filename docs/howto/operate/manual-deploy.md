# Set up and use the the deployment scripts locally

While deploys generally go through our GitHub Actions workflow, sometimes you
need to deploy from your laptop - primarily when testing changes on staging or
actively fixing an outage. This isn't ideal, but this is where we are now.

Our deployment scripts live in the [`deploy/`](https://github.com/2i2c-org/pilot-hubs/blob/master/deploy.py)
of this repository, and can deploy one or more hubs to our clusters. 


## Setting up local environment

1. Create a virtual environment for use with this repository

   ```bash
   python3 -m venv .
   source bin/activate
   ```

   You can also use `conda` if you prefer instead.

2. Install python packages required by our deployment script
   
   ```bash
   pip install -r requirements.txt
   ```

3. Install the [Google Cloud SDK](https://cloud.google.com/sdk) so
   our scripts can authenticate to Google Cloud Platform for access
   to our secret keys. Note that we use Google Cloud Platform (with
   [`sops`](https://github.com/mozilla/sops) secure secrets *stored
   in this repository* - so you would need the google cloud sdk regardless of
   the final location of the hub itself.

4. Authenticate to Google Cloud Platform! First, you should run
   `gcloud auth login` and follow the prompts - this authenticates your
   `gcloud` commandline tool. Next, you should run `gcloud auth application-default login`,
   and follow the prompts - this authenticates you to any tools that
   want to authenticate to Google Cloud *on your behalf* - including
   our deploy scripts! See [Application Default Credentials](https://cloud.google.com/docs/authentication/production#automatically)
   for more information.

5. We use [`sops`](https://github.com/mozilla/sops) for secret management.
   We use `sops` with [Google KMS key](https://cloud.google.com/security-key-management) to
   automatically encrypt/decrypt files when needed. So access to
   the KMS key grants access to the secrets. Setting up the
   application default login in step 4 means sops can use that
   to decrypt the secrets when necessary. The key currently in use is
   in the `two-eye-two-see` GCP project, so you must already have
   access to it to decrypt the files

   You can test it by running `sops config/secrets.yaml`, and checking
   if your `$EDITOR` pops up with the decrypted contents of the secret
   file.

## Doing a deploy

1. Make the [config change](../topic/config.md) you want to deploy.

2. Deploy just a single hub:

   ```bash
   python3 deployer deploy <cluster-name> <hub-name>
   ```

   The script will look for a hub named `<hub-name>` in the cluster config
   defined at `config/hubs/<cluster-name>.cluster.yaml`.

3. You can deploy to *all* hubs on a given cluster by omitting the hub name.
   
   ```bash
   python3 deployer deploy <cluster-name>
   ```

```{note}
You should mostly use the `staging` hub in the `2i2c` cluster for testing.
```