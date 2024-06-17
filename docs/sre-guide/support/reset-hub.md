# Reset a Hub

Some hubs are used "seasonally", and need to be "reset" after the end of the workshop /
event. This helps save on disk space as well as keep the admin interface clean.

This is a *destructive* action, so should only be done in consultation with the
community champion. Let them know what's going to happen, and await confirmation
before performing the action. You can use the following template.

```{note}
We are going to "reset" the hub. This would do the following:

1. Remove **all** user home directories. The *shared* directories would not be
   touched, but you can clean them up yourself if you need.

2. Remove all the users from the admin view, except 2i2c engineers and those explicitly
   marked as admins via our configuration. Those are:

   {{ list of admin users from the config.yaml file for this hub}}

This will also forcibly log out and stop the server of any user running at that time.

Let us know if this sounds ok, and we will proceed!
```

Once they respond affirmatively, you can begin.

## Delete all home directories

This clears up space and reduces their cloud costs.

1. Get a shell with the home directories mounted

   ```bash
   deployer exec homes <cluster-name> <hub-name>
   ```

   This may take 30s-1minute.

2. Look for directories with the word `shared` in them. Normally you would only
   find `_shared-public` and `_shared`, but check just in case there's another one.
   We don't want to accidentally delete anything else!

   ```bash
   cd /home
   ls | grep shared
   ```

   If you find other directories named shared, escalate to the engineering slack channel
   to help figure out what to do next.

3. Delete everything other than the shared directories. This may take a while (upto a hour)
   depending on the size of the home directories.

   ```bash
   ls /home | grep -v -P "_shared|_shared-public" | xargs rm -rf
   ```

4. Exit out of the pod, as you're done now!

   ```bash
   exit
   ```

## Clear out existing list of users

This keeps the admin interface clean, which is quite helpful for workshop hubs.

1. Make sure that there are no user servers running. If they are, stop them.

   ```bash
   deployer use-cluster-credentials <cluster-name>
   kubectl -n <hub-name> delete pod -l component=singleuser-server
   ```

2. The easiest way to do this is to simply clean out the `sqlite` db that JupyterHub
   uses to store information. Get a shell on the hub pod for this hub:

   ```bash
   deployer exec hub <cluster> <hub>
   ```

3. Rename the `jupyterhub.sqlite` file to a different name. This way, we preserve the db
   if we need it for some reason in the future, but also force JupyterHub to create one
   from scratch.

   ```bash
   mv jupyterhub.sqlite jupyterhub.sqlite.$(date --iso-8601)
   exit # we are done, get out.
   ```

   This will create a `jupyterhub.sqlite.<current-date>` file.

4. We now need to restart the JupyterHub process. The easiest way to do that is to kill
   the JupyterHub pod, so kubernetes will bring up a new one.

   ```
   deployer use-cluster-credentials <cluster-name>
   kubectl -n <hub-name> delete pod -l component=hub
   ```

   The hub pod should restart, and everything should be fine now.

## Notify the community

Once this is done, let the community know the process has been completed.
