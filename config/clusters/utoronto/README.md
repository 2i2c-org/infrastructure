# University of Toronto README

This file documents some of the choices made in the UToronto cluster,
which serves multiple hubs.

## Staging Hubs

Each hub gets its own staging hub. They match all configuration, except:

1. Home directory storage is different, for security isolation
2. Different Login credentials
3. (Possibly) different hub DB sizes, as we still store logs in the hub db dir
   (a bad practice we should stop soon).
   
## Usernames

The default hub (at jupyter.utoronto.ca) and its staging hub use an opaque
id (oid) in the form of a [uuid](https://en.wikipedia.org/wiki/Universally_unique_identifier)
as usernames. This caused a bunch of confusion with respect to support, and
hence other hubs use user emails as usernames instead.
   
## Config Structure

For each hub, we want the following files:

1. `<hub-name>-common.values.yaml` - common values for prod & staging hubs
2. `<hub-name>-staging.values.yaml` - staging config overrides
3. `<hub-name>-prod.values.yaml` - prod config overrides
4. `enc-<hub-name>-staging.secret.values.yaml` - `sops` encrypted config for staging
5. `enc-<hub-name>-prod.secret.values.yaml` - `sops` encrypted config for prod

There is also a `common.values.yaml` that is common to *all* the hubs.
