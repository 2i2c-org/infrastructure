# CILogon: switch Identity Providers or user accounts

By default, logging in with a particular user account will persist your credentials in future sessions.
This means that you'll automatically reuse the same institutional and user account when you access the hub's home page.

## Switch Identity Providers

1. **Logout of the Hub** using the logout button or by going to `https://{hub-name}/hub/logout`.
2. **Clear browser cookies** (optional). If the user asked CILogon to reuse the same Identity Provider connection when they logged in, they'll need to [clear browser cookies](https://www.lifewire.com/how-to-delete-cookies-2617981) for <https://cilogon.org>.

   ```{figure} ../../images/cilogon-remember-this-selection.png
   The dialog box that allows you to reuse the same Identity Provider.
   ```

   Firefox example:
   ```{figure} ../../images/cilogon-clear-cookies.png
   An example of clearing cookies with Firefox.
   ```

3. The next time the user goes to the hub's landing page, they'll be asked to re-authenticate and will be presented with the list of available Identity Providers after choosing the CILogon connection.
4. They can now choose **another Identity Provider** via CILogon.

```{note}
If the user choses the same Identity Provider, then they will be automatically logged in with the same user account they've used before. To change the user account, see [](troubleshoot:cilogon:switch-user-accounts).
```

(troubleshoot:cilogon:switch-user-accounts)=
## Switch user accounts

1. Logout of the Hub using the logout button or by going to `https://{hub-name}/hub/logout`.
2. Logout of CILogon by going to the [CILogon logout page](https://cilogon.org/logout).
3. The next time the user goes to the hub's landing page, they'll be asked to re-authenticate and will be presented with the list of available Identity Providers after choosing the CILogon connection.
4. Choose the **same Identity Provider** to login.
5. The user can now choose **another user account** to login with.

# 403 - Unauthorized errors

If you see a 403 error page, this means that the account you were using to login hasn't been allowed by the hub administrator.

```{figure} ../../images/403-forbidden.png
```

If you think this is an error, and the account should have been allowed, then contact the hub administrator/s.

If you used the wrong user account, you can log in using another account by following the steps in [](troubleshoot:cilogon:switch-user-accounts).
