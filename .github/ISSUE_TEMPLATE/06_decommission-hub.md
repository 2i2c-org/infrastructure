---
name: "\U0001F4E6 Decommission a Hub"
about: Decommission a Hub that is no longer in active use
title: "[Decommission Hub][{{ deadline }}] {{ HUB NAME }}"
labels: ''
assignees: ''

---

### Summary

<!-- Please provide a short, one-sentence summary around why this Hub should be decommissioned.
Usually, it is because it was a hub that we created for a workshop/conference and the event has now passed. -->

### Info

- **Community Representative:** <!-- The GitHub ID of the current representative for the Hub and Community, e.g. @octocat -->
- **Link to New Hub issue:** <!-- The link to the original issue to create the hub, e.g. https://github.com/2i2c-org/infrastructure/issues/#NNN -->
- **Proposed end date:** <!-- The date by which the hub should be out of service. This should have been mentioned in the New Hub issue above so can be copy-pasted. Otherwise, leave blank and negotiate with the Community Representative. -->

### Task List

#### Phase I

- [ ] Confirm with Community Representative that the hub is no longer in use and it's safe to decommission
- [ ] Confirm if there is any data to migrate from the hub before decommissioning
  - [ ] If yes, confirm where the data should be migrated to
    - [ ] Confirm a 2i2c Engineer has access to the destination in order to complete the data migration
  - [ ] If no, confirm it is ok to delete all the data stored in the user home directories

#### Phase II - Hub Removal

(These steps are described in more detail in the docs at https://infrastructure.2i2c.org/hub-deployment-guide/hubs/delete-hub/)

- [ ] Manage existing home directory data (migrate data from the hub or delete it)
- [ ] Manage existing cloud bucket data (migrate data, or delete it)
- [ ] Delete the hub's authentication application on GitHub or CILogon (note CILogon removal requires the hub config in place)
- [ ] Remove the appropriate `config/clusters/<cluster_name>/<hub_name>.values.yaml` files. A complete list of relevant files can be found under the appropriate entry in the associated `cluster.yaml` file.
- [ ] Remove the associated hub entry from the `config/clusters/<cluster_name>/cluster.yaml` file.
- [ ] Remove the hub deployment
  - TIP: Run `deployer use-cluster-credentials <cluster_name>` before running the commands below
  - `helm --namespace HUB_NAME delete HUB_NAME`
  - `kubectl delete namespace HUB_NAME`

#### Phase III - Cluster Removal

_This phase is only necessary for single hub clusters._

- [ ] Remove the cluster's datasource from the central Grafana with:
  - `deployer grafana central-ds remove <cluster_name>`
- [ ] Run `terraform plan -destroy` and `terraform apply` from the [appropriate workspace](https://infrastructure.2i2c.org/en/latest/topic/terraform.html#workspaces), to destroy the cluster
- [ ] Delete the terraform workspace: `terraform workspace delete <NAME>`
- [ ] Delete the terraform values file under the `projects` folder associated with the relevant cloud provider (e.g. `terraform/gcp/projects/` for GCP)
- [ ] Remove the associated `config/clusters/<cluster_name>` directory and all its contents
- Remove the cluster from CI:
  - [ ] [`deploy-hubs.yaml`](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/deploy-hubs.yaml)
  - [ ] [`deploy-grafana-dashboards.yaml`](https://github.com/2i2c-org/infrastructure/blob/HEAD/.github/workflows/deploy-grafana-dashboards.yaml)
- [ ] Remove A record from Namecheap account

### Definition of Done
_A non-specific, pre-defined list of tasks that should be considered before marking the task complete._
- [] All the tasks above have been completed
- [] Existing functionality was not broken
