# Extra Scripts

This folder contains some extra scripts that are not run as part of day-to-day operations, but can reduce the toil of some manual processes we undertake occasionally.

- **[`rsync-active-users.py`](./rsync-active-users.py):** This script uses `rsync` to synchronise the home directories of active users of a JupyterHub in parallel.
  This script is useful to run when migrating a hub.
