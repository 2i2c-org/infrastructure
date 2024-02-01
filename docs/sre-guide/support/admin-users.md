# Adding admin users based on a support request

Requests to make specific users admin are handled via Freshdesk.

1. Validate that the person asking is allowed to ask for this

2. Make sure that the username is in the correct format for the hub!
   This means GitHub handles for GitHub Auth, appropriate values based on
   `username_claim` for CILogon based setup, and look for examples under
   existing admin list for any custom auth setups we may have.

   If it looks like the username format is invalid, ask them to go to
   `{{ hub-url }}/hub/home` and tell us the username they see on the top right.
   This is always correct.

3. Add the username provided to admin users, under `hub.config.Authenticator.admin_users`.
   Add a comment linking to the freshdesk ticket that required us to add this next
   to the username.

4. Make a pull request with this change, and you can self merge this.

5. Let the requestor know this has been deployed. You may use the following template:

   > Hello {{ Name }}
   >
   > The usernames you provided have been made admins on the JupyterHub! You can verify
   > this by going to the hub control panel at {{ hub-url }}/hub/home, and you should
   > see an 'Admin' option in the top bar.
   >
   > Thanks!

## Caveats & future work

We don't have a clearly stated policy on whether admin access should
be granted via config or via existing admins marking other users as
admin. Marking other users as admins via the admin interface may
cause them to lose that status if we ever have to nuke and redeploy
the hub's database. This lack of clarity in our policy is why we don't
just tell them to use the admin interface if they email support