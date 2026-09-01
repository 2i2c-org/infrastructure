# Extra Scripts

This folder contains some extra scripts that are:

- not run as part of day-to-day operations, but can reduce the toil of some manual processes we undertake occasionally.

## List of scripts with brief descriptions

- **[`rsync-active-users.py`](./rsync-active-users.py):** This script uses `rsync` to synchronise the home directories of active users of a JupyterHub in parallel.
  This script is useful to run when migrating a hub.
- **[`analyze-spawn-timing.py`](./analyze-spawn-timing.py):** This script reconstructs user-server spawn timelines from the Kubernetes Events we ship to CloudWatch Logs.
  It reports where boot time goes (node scaling, image pulls, other) as distributions, breakdowns by node type or image, day/week trends, and the individual fastest and slowest spawns with the configuration behind them.
  Run it against a cluster (`--cluster maap`) or a saved events file (`--from-file`); see the module docstring for examples.
