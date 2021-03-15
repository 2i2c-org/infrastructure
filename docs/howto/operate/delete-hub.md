# Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.
2. **Backup the home directory contents**. Especially if we think that users will want this information in the future (or if we plan to re-deploy a hub elsewhere).
3. **Delete the Helm namespace**. Run `helm -n <hub-name> delete <hub-name>`.
4. **Delete our Authentication entry**. If the hub hasn't been recreated anywhere, remove the entry from `auth0.com`
