# Give Grafana access to community representative

```{note}
This is only available when the community's hub is running on a **dedicated cluster**, as
Grafana has information about **all** the hubs on a given cluster.
```

Our community representatives might want access to the Grafana dashboard for their hub,
to provide useful information about usage as well as diagnostic information when things
are not working as they should. In the longer term, we should streamline this ([issue](https://github.com/2i2c-org/infrastructure/issues/1850)).
However, for now, we can **invite** individual users to a grafana via the Grafana UI.

1. Find the appropriate grafana for this community - usually it is at `https://<grafana>.<community>.2i2c.cloud`.
   You can find the correct value by looking at the `support.values.yaml` file inside `config/clusters/<cluster-name>`.

2. Login as an admin user. The username is `admin`, and the password can be found in the file
   `helm-charts/support/enc-support.secret.values.yaml`. As it is an encrypted file, you need to run
   `sops helm-charts/support/enc-support.secret.values.yaml` to be able to see the password.
   
   ```{warning}
   This password is **shared** across all our Grafanas! So treat it with care, and do not share it with
   others
   ```

3. Hover over the gear icon in the bottom of the left sidebar, select 'Users'.

4. Click the blue 'Invite' button on the main area.

5. Enter the email address of the community representative we want to create an account for. Leave the
   name blank (they can fill it in later if they wish). Give them an **Admin** role (so they can invite others
   if needed). Deselect 'Send invite email' as that does not actually work for us anyway (we do not have outgoing
   email configured). Click **Submit**

6. You will be brought back to the Users page. To the left of the 'Invite' button, you'll see a button named
   'Pending Invites'. Click that.
   
7. Find the invite for the user you just added, and click the 'Copy Invite' button for that user. This will copy an
   **Invite link** for that user, that can be sent back to the community representative! They should be able to click the
   link, and create an account in the Grafana to have access to all the dashboards.
   
   ```{warning}
   Anyone posessing this invite link can access the grafana, so make sure to not leak it!
   ```

