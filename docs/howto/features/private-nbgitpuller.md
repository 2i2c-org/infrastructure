# Allow nbgitpuller to pull from private GitHub repos

[nbgitpuller](https://github.com/jupyterhub/nbgitpuller) is very popularly
used to pull repos from public GitHub repositories. We can also allow users
to pull from *private* GitHub repositories, with [git-credential-helpers](https://github.com/yuvipanda/git-credential-helpers).

## Configure the image

The image used in the JupyterHub must have the [git-credential-helpers](https://pypi.org/project/git-credential-helpers/)
package installed from PyPI. Unfortunately this is currently not installed in
any common upstream images, so this will only work with custom images.

## Setup GitHub app

`git-credentials-helper` uses a [GitHub App](https://docs.github.com/en/developers/apps)
to pull private repos. So you first need to create a GitHub app for each hub that wants
to pull private repos as static content.

1. Create a [GitHub app in the 2i2c org](https://github.com/organizations/2i2c-org/settings/apps/new).

2. Give it a descriptive name (such as '<hub-name> private repo access') and description, as users will see this when authorizing
   access to their private repos.

3. Disable webhooks (uncheck the 'Active' checkbox under 'Webhooks'). All other
   textboxes can be left empty.

4. Under 'Repository permissions', select 'Read' for 'Contents'.

5. Under 'Where can this GitHub App be installed?', select 'Any account'. This will
   enable users to push to their own user repositories or other organization repositories,
   rather than just the 2i2c repos.

6. Create the application with the 'Create GitHub app' button.

7. Copy the numeric 'App id' from the app info page you should be redirected to.

8. Create a new private key for authentication use with the `Generate a private key`
   button. This should download a private key file, that you should delete after
   putting it in the appropriate config (in the next step)

## Helm values configuration

Now, we configure our user servers to authenticate themselves with GitHub using
the app we just created.

1. Tell `git` to use our GitHub app for authenticating when cloning from GitHub.

   ```yaml
   jupyterhub:
     singleuser:
       extraFiles:
         gitconfig:
           mountPath: <path-to-git-config>
           stringData: |
             [credential "https://github.com"]
             helper = !git-credential-github-app --app-key-file /etc/github/github-app-private-key.pem --app-id <app-id>
             useHttpPath = true
   ```
   
   Unfortunately, the `<path-to-git-config>` depends on *how* `git` is
   installed inside the image. 

   a. The most common situation is `git` is installed from `apt` or the system
      package manager, and not `conda`. In this case, `mountPath` is `/etc/gitconfig`.
      
   b. If `git` is installed from conda, it will
      *not* read `/etc/gitconfig` (see [bug](https://github.com/conda-forge/git-feedstock/issues/113),
      but `${CONDA_PREFIX}/etc/gitconfig`. So, *if* the image installs `git` from
      conda-forge, you have to start the image, look for the value of the `${CONDA_PREFIX}` environment variable, and construct `mountPath` to be `${CONDA_PREFIX}/etc/gitconfig`

   Use the app-id of the GitHub app you just created. This goes in the hub's
   `values.yaml` file. If used for a `daskhub`, next the whole thing under a
   `basehub` key.

2. Create a sops-encrypted file (usually in the form of
   `enc-<hub-name>.secret.values.yaml`) to hold the secret values required to authenticate
   the GitHub app.

   ```yaml
   jupyterhub:
     singleuser:
       extraFiles:
         github-app-private-key.pem:
           mountPath: /etc/github/github-app-private-key.pem
           stringData: |
             <contents-of-the-private-key-file>
            
   ```
   
   Make sure this file is also listed under `helm_chart_values_files` for the hub in
   the cluster's `cluster.yaml` so it is read during deployment.

3. Once set up, do a deploy to test!

## Grant access to the private repo

Finally, someone with admin rights on the private repo to be pulled needs to
grant the github app we just setup access to the private repo. **This is the only
part that hub admins rather than 2i2c engineers need to do**.

1. Go to the 'Public page' of the GitHub app created. This usually is of the
   form `https://github.com/apps/<name-of-app>`. You can find this in the information
   page of the app after you create it, under 'Public link'

2. Install the app in the organization the private repo is in, and grant it access
   *only* to the repo that needs to be pulled.


## Create the nbgitpuller link

An nbgitpuller link can be created now for this private repo with the usual
mechanisms:

1. The [nbgitpuller.link](http://nbgitpuller.link) generator
2. The [Firefox](https://addons.mozilla.org/en-US/firefox/addon/nbgitpuller-link-generator/) or [Chrome](https://chrome.google.com/webstore/detail/nbgitpuller-link-generato/hpdbdpklpmppnoibabdkkhnfhkkehgnc)
   extensions.
