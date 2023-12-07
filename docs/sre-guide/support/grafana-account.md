(grafana-access:invite-link)=
# Give Grafana access to a community representative

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
   Alternatively, this secret is also available in the [shared BitWarden vault](https://vault.bitwarden.com/#/vault?organizationId=11313781-4b83-41a3-9d35-afe200c8e9f1).

   ```{warning}
   This password is **shared** across all our Grafanas! So treat it with care, and do not share it with
   others
   ```

3. Expand the ["hamburger" menu](https://en.wikipedia.org/wiki/Hamburger_button) on the
   left-hand-side, then expand the "Administration" sub-menu (denoted by a gear icon),
   and then select "Users".

   ```{figure} ../../images/grafana-grant-access_step-3a.jpg
   Location of the "hamburger" menu on the Grafana dashbaord
   ```

   ```{figure} ../../images/grafana-grant-access_step-3b.jpg
   Expand the "Administration" sub-menu, and then select "Users"
   ```

4. Select "Organization users", and then select the blue "Invite" button on the right-hand-side.

   ```{figure} ../../images/grafana-grant-access_step-4a.jpg
   Select the "Organization users" tab
   ```

   ```{figure} ../../images/grafana-grant-access_step-4b.jpg
   Select the blue "Invite" button on the right-hand-side
   ```

5. Enter the email address of the community representative we want to create an account for. Leave the
   name blank (they can fill it in later if they wish). Give them an **Admin** role (so they can invite others
   if needed). Deselect 'Send invite email' as that does not actually work for us anyway (we do not have outgoing
   email configured). Click **Submit**.

   ```{figure} ../../images/grafana-grant-access_step-5.jpg
   Input the email address of the community representative. Give them the "Admin" role.
   Toggle off the "Send invite email" option.
   ```

6. You will be brought back to the Users page. Select the "Organization users" tab again, and now to the left
   of the 'Invite' button, you'll see a button named 'Pending Invites'. Click that.

   ```{figure} ../../images/grafana-grant-access_step-6.jpg
   Select the 'Pending Invites' option from the 'Organization users' tab
   ```

7. Find the invite for the user you just added, and click the 'Copy Invite' button for that user. This will copy an
   **Invite link** for that user, that can be sent back to the community representative! They should be able to click the
   link, and create an account in the Grafana to have access to all the dashboards.

   ```{figure} ../../images/grafana-grant-access_step-7.jpg
   Select the "Copy invite" button next to the user you just created
   ```

   ```{warning}
   Anyone posessing this invite link can access the grafana, so make sure to not leak it!
   ```
