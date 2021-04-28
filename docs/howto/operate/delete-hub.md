# Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.

2. **Backup the home directory contents**.  Especially if we think that
   users will want this information in the future (or if we plan to re-deploy a
   hub elsewhere).

3. **Delete the Helm release**. In the appropriate cluster,
   run `helm -n <hub-name> delete <hub-name>`

4. **Delete the kubernetes namespace**. In the appropriate cluster, run
   `kubectl delete namespace <hub-name>`, to cleanup any possible leftovers that
   step (3) missed

5. **Delete our Auth0 application**.  For each hub, we create an
   [Application](https://auth0.com/docs/applications) in Auth0.  There is a
   limited number of Auth0 applications available, so we should delete the one
   used by this hub when it's done.  You should be able to see the [list of
   applications](https://manage.auth0.com/dashboard/us/2i2c/applications) if you
   login to auth0 with your 2i2c google account.
