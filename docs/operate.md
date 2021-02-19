# Operating the hubs

Information about operating the hubs, debugging problems, and performing common actions.

(operate:team-process)=
## Team process for hub development and operation

### Issues to track hubs

When a new hub is created, [create a new GitHub issue for the hub](https://github.com/2i2c-org/pilot-hubs/issues/new) using the "New Hub" template.
This issue is a "meta" issue that tracks the state of this hub over time.
These issues serve both as a "Source of Truth" of information about the hub, as well as a place for conversation around operating that hub.
As task issues are created, cross-link them to a hub if they are specifically about that hub.

### Team goals

Team goals are higher-level goals that are usually less-concrete (AKA, there's no single action that will "complete" them) and span a longer period of time.

We keep track of team goals via the [{guilabel}`goal` label in GitHub](https://github.com/2i2c-org/pilot-hubs/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Agoal).

### Team tasks

Team tasks are specific, actionable things that must be done (usually they related to development work on the 2i2c Hubs).
We keep track of team task via the [{guilabel}`task` label in GitHub](https://github.com/2i2c-org/pilot-hubs/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Atask).

### Bi-weekly task syncs

Every other Monday, the 2i2c Hub Operations team conducts a team sync to get on the same page and coordinate their work for the week.

% CHRIS proposes that we move the "process" sections from here and integrate them into https://2i2c.org/team-compass/team/tech/coordination/#bi-weekly-team-syncs

% TODO: here's a rough proposal, need to flesh this out
- We modify the process described here: https://2i2c.org/team-compass/team/tech/coordination/#bi-weekly-team-syncs
- Add these steps to the team member check-in:
  - Link to any tasks that were completed in the last window
  - Highlight any tasks that need help from others
  - Note the tasks that they're assigning themselves to for the next 2 week window.
  - Provide updates about any goals that they've added themselves to.

```{note}
While these syncs happen every two weeks, the process of assigning oneself to tasks, completing them, etc can be dynamic and constantly updating.
The syncs are just to get everyone on the same page.
```

## Adding a new hub

Adding a new hub requires that we do three things:

1. [Create a new GitHub issue for the hub](https://github.com/2i2c-org/pilot-hubs/issues/new).
2. Create the hub via appending a new entry in the `hubs.yaml` file (see [](configure.md) for more information).
3. Start following [team process](operate:team-process) around operating the hubs.


## Gain `kubectl` & `helm` access to a hub

Each of the hubs in the 2i2c Pilot runs on Google Cloud Platform and Kubernetes.
To access the Kubernetes objects (in order to inspect them or make changes), use
the `kubectl` command line tool.

% TODO: Add something about what helm does here

### Project Access

First, you'll need to access the Google Cloud projects on which the hubs run. The most accurate name
of the project can be gleamed from `hubs.yaml` (under `gcp.project` for each cluster entry). Currently,
the projects are:

| Cluster | Project Name |
| - | - |
| *.pilot.2i2c.cloud | `two-eye-two-see` |
| *.cloudbank.2i2c.cloud | `cb-1003-1696` |

If you don't have access to these, please get in touch with 2i2c staff.

### Commandline tools installation

You can do all this via [Google Cloud Shell](https://cloud.google.com/shell),
but might be easier to do this on your local machine. You'll need the following
tools installed:

1. [gcloud](https://cloud.google.com/sdk)
2. [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
3. [helm](https://helm.sh/)

### Authenticating

First, you need to [gcloud auth login](https://cloud.google.com/sdk/docs/authorizing#authorizing_with_a_user_account),
so you can perform `gcloud` operations. Next, you need to do [gcloud auth application-default login](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login)
so `kubectl` and `helm` could use your auth credentials.

### Fetch Cluster credentials

For each cluster, you'll need to fetch credentials at least once with [gcloud container clusters get-credentials](https://cloud.google.com/sdk/gcloud/reference/container/clusters/get-credentials).

```bash
gcloud container clusters get-credentials <cluster-name> --region <region> --project <project-name>
```

You can get authoritative information for `<cluster-name>`, `<zone>` and `<project-name>` from
`hubs.yaml`.

With that, `kubectl` and `helm` should now work! 

### (Optional) Access via Google Cloud Shell

Instead of setting up the tools & authenticating locally, you can do all this via
[Google Cloud Shell](https://cloud.google.com/shell). It has all the tools installed,
and the authentication done. Instead of doing `gcloud container clusters get-credentials`
yourself, you can instead:


1. Go to the [Google Cloud Kubernetes Engine page](https://console.cloud.google.com/kubernetes/list) (for the appropriate project)

2. Click on `Connect`, as seen in the figure below.

   ````{panels}
   ```{figure} images/gcp-k8s-dashboard.png
   ```
   ---
   ```{figure} images/gcp-run-in-shell.png
   ```
   ````

3. This will spin up an interactive cloud shell where you have `kubectl` access.

## Delete a hub

If you'd like to delete a hub, there are a few steps that we need to take:

1. **Backup the hub database**. Backup the `jupyterhub.sqlite` db off the hub.
2. **Backup the home directory contents**. Especially if we think that users will want this information in the future (or if we plan to re-deploy a hub elsewhere).
3. **Delete the Helm namespace**. Run `helm -n <hub-name> delete <hub-name>`.
4. **Delete our Authentication entry**. If the hub hasn't been recreated anywhere, remove the entry from `auth0.com`

## Access the Hub Grafana Dashboards

Each 2i2c Hub is set up with [a Prometheus server](https://prometheus.io/) to generate metrics and information about activity on the hub, and each cluster of hubs has a [Grafana deployment](https://grafana.com/) to ingest and visualize this data.

The Grafana for each cluster can be accessed at `grafana.<cluster-name>.2i2c.cloud`.
For example, the pilot hubs are accessible at `grafana.pilot.2i2c.cloud`. You'll need
a username and password to access each one. Ask one of the 2i2c team members for access.
