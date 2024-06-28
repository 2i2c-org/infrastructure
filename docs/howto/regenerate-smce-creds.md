(nasa-smce:regenerate-password)=
# Regenerate a password for a user in a NASA SMCE account

The AWS accounts associated with NASA's [Science Managed Cloud Environment](https://smce.nasa.gov)
have a 60 day password expiry policy. If someone on the team misses this
deadline, we can actually reset passwords for each other!

1. Someone in the team with access logs into the AWS console of the appropriate project
2. Follow [AWS's user guide on resetting passwords](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_admin-change-user.html#id_credentials_passwords_admin-change-user_console)
   for whoever's 60 day window has elpased
3. In addition, a `AccountDisabled` IAM Group will be automatically added to the
   user whenever their credentials expire, and this will show up as a "cannot
   change password" error when the user logs in next. So the user should also be
   removed from this group. You can do so from under the "Groups" tab in the
   AWS console when looking at the details of this user.
