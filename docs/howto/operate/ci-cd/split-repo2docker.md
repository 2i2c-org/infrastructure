# Split up an image for use with r2d-action

Sometimes we have user images defined in a repo, and we want to extract
it to a standalone repo so it can be used with the [repo2docker action](https://github.com/jupyterhub/repo2docker-action).
But we want to retain full history of the image still, so we can look
back and see why things are the way they are, as well as credit the people
who contributed over time. This page documents the git-fu required to
make this happen.

1. Clone the base repository you are extracting the image from.
   We will be performing destructive operations on this clone,
   so it has to be a fresh clone.

    ```bash
    git clone <base-repo-url> <hub-image> --origin source
    ```

    We name the directory `<hub-image>` as that would be the name of the
    repo with just the user image. We ask git to name the remote it creates be
    called `source`, as we will create a new GitHub repo later that will be `origin`.

2. Make sure [git-filter-repo](https://github.com/newren/git-filter-repo)
   is installed. It should be available in [brew or other package managers](https://github.com/newren/git-filter-repo/blob/main/INSTALL.md)

3. Run `git-filter-repo` to remove everything from the repo except the
   image directory.

   ```bash
    git filter-repo --subdirectory-filter <path-to-image-directory> --force
    ```

    The repo root directory now contains the contents of `<path-to-image-directory>`,
    as well as full git history for any commits that touched it! This way,
    we do not lose history or attribution.

4. Create a user image repository in GitHub based off [this template](https://github.com/2i2c-org/hub-user-image-template).
   The template makes it much easier to setup repo2docker-action on it.

5. Add the new user image repo as a remote you can push commits to / pull commits from.
   This will be the primary location of this repo now, so let's call it `origin`.

   ```bash
   git remote add origin git@github.com:<your-org-or-user-name>/<your-repo-name>.git
   ```

6. Fetch the new repo and check out the `main` branch, as that is the final
   destination for our image contents.

   ```bash
    git fetch origin
    git checkout main
    ```

7. Remove the `environment.yml` file from the repo - it is present as an example
   only, and we have our own we are bringing.

   ```bash
   git rm environment.yml
   git commit -m 'Remove unused environment.yml file'
   ```

8. Merge the branch we prepared earlier with just our image contents into this
   `main` branch, while telling git to not freak out about them being from different
   repos initially.

   ```bash
   git merge staging --allow-unrelated-histories  -m 'Bringing in image directory from deployment repo'
   git push origin main
   ```

   In this case, `staging` was the name of the branch in the source
   repo, and `main` is the name of the main branch in the new user image
   repo.

9. Now follow the instructions in the README of your new repo to complete setting up
   the repo2docker action as well as using this on your hub!