# Anonymize usernames with CILogon

By default, we use a human readable identifier - like email or username -
when logging a user in. This is familiar to most users, makes support easier,
and usually not a problem. However, in some specific cases, we might need to
reduce the amount of Personally Identifiable Information ([PII](https://en.wikipedia.org/wiki/Personal_data))
stored in the system, and so emails or usernames may not be viable. We offer
a way to anonymize usernames if absolutely needed.

## Do you really need this?

. Usernames will now look like gibberish (`j77eci3dubsngx76m4ssd5sh6z3uiomgdrkvjymoxruigcystuva`, not `yuvipanda`), confusing many users. It almost looks like
a password! When needing to provide support to users, they *must* log in to
the hub, go to the Control Panel, and find their username. If they can't
do this, there is no real way to identify the user for support. This is
a **major** disadvantage, so seriously consider if you really really need this.

Moving away from this after the fact is also close to impossible, and changing
authentication providers (away from CILogon) is also impossible, without losing
all existing users' home directories.

So, very seriously consider if you need this before you enable it!

## How does it work?

Given that anonymizing usernames comes at a cost, it **must** provide us some
useful privacy guarantees to be worth it. Those are:

1. We must not possess, *stored at rest*, a user identifier that is Personally
   Identifiable. This includes usernames, emails, as well as opaque integer
   user ids from external services. For example, if we were to use the numerical 
   user id from GitHub (via the `oidc` attribute from CILogon), it can
   be trivially mapped back to the username [via
   BigQuery](https://www.gharchive.org/#bigquery) or any number of
   public data sources. The numerical id is also shared with any other
   website using GitHub (or Google, etc) for login, so any data
   breaches in those websites can also be used to de-anonymize our
   users.
   
2. We live in a world where user data leaks are a fact of life, and you can buy
   tons of user identifiers for pretty cheap. This may also happen to *us*, and
   we may unintentionally leak data too! So users should still be hard to 
   de-anonymize when the attacker has in their posession the following:

   1. List of user identifiers (emails, usernames, numeric user ids,
      etc) from *other data breaches*.
   2. List of user identifiers *from us*.
   3. Any secret keys we use to hash these identifiers.
   
   (1) is out of our control, and we must be prepared for (2) and (3), so
   we truly do not store any personal information, rather than just make it
   slightly more complicated for our users to be deanonymized.
   
To provide these guarantees, we create the anonymized username in the following
way:

1. Take a combination of user attributes returned to us by CILogon. Right now,
   we pick the following:
   
   1. A CILogon specific opaque identifier (`sub`)
   2. The identifier for the 3rd party OAuth provider chosen by the user (Google,
      GitHub, Microsoft, etc) (`idp`)
   3. The internal opaque identifier used by *that* third party (`oidc`)
   
2. Combine it with a per-hub *secret salt* (or [pepper](https://en.wikipedia.org/wiki/Pepper_(cryptography)))

3. Using the pepper as the key, hash the user attributes with the
   [blake2b](https://en.wikipedia.org/wiki/BLAKE_(hash_function)) keyed
   hashing algorithm, to produce a 32byte secret. This is used as the username.
   
To now deanonymize these usernames, an attacker must have:

1. Breached user information from CILogon (for the CILogon identifier)
2. Breached user information from the third party auth provider
3. Access to the secret value we used as pepper for the hub in question

This provides a reasonable level of protection. And given that we 2i2c
don't have access to (1) or (2) at rest, even we can't deanonymize this in
the future if we turn evil.

Note, however, that we still *receive* personally identifiable information
*when the user logs in*, and we might use this for authorization purposes too.
All this *only* removes our liability for storing this data *at rest*, not
while in transit.

## Limitations

Currently, only hubs with the following configuration are supported:

1. Must use CILogon for authentication
2. Only non-institutional CILogon authentication providers are supported. This
   means Google, GitHub and Microsoft. Institutional authentication providers may
   be supported in the future.
3. All existing user accounts will become invalid.

## Authorization

We still want to be able to do **authorization** based on user attributes,
such as domain of email or explicit list of allowed emails. This is still
possible, as the anonymization step is done in `post_auth_hook` which runs
*after* the initial authorization steps are done. So `admin_users` and
`allowed_users` can be used in the same manner as used in CILogon without
anonymization turned on.

## Enabling anonymization

1. In the unencrypted config yaml file for the hub, add the following:
    ```yaml
    jupyterhub:
      custom:
        auth:
          anonymizeUsername: true
    ```

    Nest this inside a `basehub` key if this is for a daskhub.

2. Generate a secret key to be used for deriving the username, by running
   `openssl rand -hex 32` on your commandline.
   
3. In the corresponding encrypted values file for the hub, add the following 
   config:
   
   ```yaml
    jupyterhub:
      hub:
        extraEnv:
          USERNAME_DERIVATION_PEPPER: <value-generated-in-step-2>
   ```
   
   Nest this inside a `basehub` key if this is for a daskhub.
  
This should be enough configuration changes for this to work.

## Longer term solution

This is a common problem, and the longer term solution is to get CILogon to
implement [Pairwise Pseudonymous Identifiers](https://curity.io/resources/learn/ppid-intro/)

## Credit

Thanks to the `#infosec` channel on the [hangops slack](https://signup.hangops.com/)
for their help in thinking this through.
