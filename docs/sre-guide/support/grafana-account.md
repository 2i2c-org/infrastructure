(grafana-access:invite-link)=
# Give Grafana access to a community representative

```{note}
This is only available when the community's hub is running on a **dedicated cluster**, and not **shared** clusters, as Grafana has information about **all** the hubs on a given cluster.
```

During the onboarding process for hub deployments, we can grant authorized technical contacts to access Grafana with administrative privileges. Once they are logged in, they can invite others from their community to access to the dashboards.

## Steps

The following process is similar for authorized *community representatives* and *2i2c engineers*. Click on the relevant tab below where applicable.

1. Find the Grafana URL - this is usually of the form `https://<grafana>.<community>.2i2c.cloud`.
   - You can find the URL by looking at the `support.values.yaml` file inside `config/clusters/<cluster-name>`
   - You can also look at the [List of Running Hubs](../../reference/hubs.md) table, and click on the "Grafana" link

2. `````{tab-set}

   ````{tab-item} Community representative
   Login with the username and password that you set when you were first onboarded to the hub. If you have forgotten your password, please contact [support](support) to reset it.
   ````

   ````{tab-item} 2i2c engineer
   Login with the admin account. The username is `admin`, and decrypt the file
      `helm-charts/support/enc-support.secret.values.yaml` with [sops](../../reference/tools.md) to find the password. Alternatively, this secret is also available in the [shared BitWarden vault](https://vault.bitwarden.com/#/vault?organizationId=11313781-4b83-41a3-9d35-afe200c8e9f1).
      ```{warning}
      This password is **shared** across all 2i2c Grafana instances! So treat it with care, and do not share it with others.
      ```
   ````

   `````

3. Expand the ["hamburger" menu](https://en.wikipedia.org/wiki/Hamburger_button) on the
   left-hand-side, then expand the "Administration" sub-menu (denoted by a gear icon),
   and then select "Users".

   ```{figure} ../../images/grafana-grant-access_step-3a.jpg
   Location of the "hamburger" menu on the Grafana dashboard
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
   if needed). Deselect **'Send invite email'** since there is no outgoing email server configured on the Grafana instance. Click **Submit**.

   ```{figure} ../../images/grafana-grant-access_step-5.jpg
   Input the email address of the community representative. Give them the "Admin" role. Toggle off the "Send invite email" option.
   ```

   ```{tip}
   If you see an error that looks like `SMTP not configured...`, then you have not toggled off the "Send invite email" option. Please try again with the option toggled off.
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
   Anyone possessing this invite link can use it to access Grafana, so make sure to not leak it!
   ```
