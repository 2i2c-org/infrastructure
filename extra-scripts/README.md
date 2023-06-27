# Extra Scripts

This folder contains some extra scripts that are either:

- run as part of our CI/CD workflows, or
- not run as part of day-to-day operations, but can reduce the toil of some manual processes we undertake occasionally.

## List of scripts with brief descriptions

- **[`rsync-active-users.py`](./rsync-active-users.py):** This script uses `rsync` to synchronise the home directories of active users of a JupyterHub in parallel.
  This script is useful to run when migrating a hub.
- **[`comment-deployment-plan-pr.py`](./comment-deployment-plan-pr.py):** This script will download a deployment plan from a GitHub Actions workflow artifact and post it to the PR that generated it.
  This helps engineers understand the 'blast radius' of their PRs.
  Executed by the [`comment-deployment-plan-pr.yaml` workflow](../.github/workflows/comment-deployment-plan-pr.yaml).
- **[`comment-test-link-merged-pr.py`](./comment-test-link-merged-pr.py):** This script will comment a link to a GitHub Actions workflow run, triggered by a merged PR, to the PR that triggered it.
  This helps engineers locate which workflows they should monitor after merging PRs.
  Executed by the [`comment-test-link-merged-pr.yaml` workflow](../.github/workflows/comment-test-link-merged-pr.yaml).
