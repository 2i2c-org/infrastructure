# Decrypt encrypted information sent to `support@2i2c.org`

Sometimes community representatives need to send us *encrypted* information -
usually credentials for cloud access or an authentication system. We use
[age](https://age-encryption.org/) (pronounced *aghe*) to allow such information to
be encrypted and then sent to use in a way that *anyone* on the team can decrypt,
rather than the information be tied to a single engineer.

## Pre-requisites

Before you can decrypt received messages, you need the following pre-requisites setup.

1. [Install age](https://github.com/FiloSottile/age#installation)
2. [Install sops](tools:sops)
3. [Authenticate with gcloud](tools:gcloud:auth) so sops can decrypt the private age
   key kept in the repository.

These are all one-time tasks, and (2) and (3) are generally required for deployments to work.

## Decrypt received message

The encrypted message looks something like

```
-----BEGIN AGE ENCRYPTED FILE-----
YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSB5cDRlMzVzWHpWU1JIeVBj
YnBqOHc5NzA3ZTZiNlljSkRDMFpyMkNUWVhBCmRBb1ltQVNPVExNK1ppbVY4OC93
OVBqUmtMQytsQkpMZkxDbXZ2R0d6ZzQKLS0tIGlGNktqWDFZMDZaYTVFTUIyNmZD
dnY1aHZGMFRpb2djMmViSU5qNkJ0M1EKtRkajujtLCgCZkPRQEGanAavNj/GQc/g
xQemDwYveQVheTyc9zA=
-----END AGE ENCRYPTED FILE-----
```

Once you have the encrypted contents, you can decrypt it by:

1. Run `deployer decrypt-age` from the infrastructure repo checkout
2. Paste the encrypted message in your terminal
3. Press enter, and then `Ctrl+D`
4. You'll see the decrypted output!

Alternatively, you can also run `deployer decrypt-age --encrypted-file-path <path-to-encrypted-file>`
if the encrypted message is stored in a file