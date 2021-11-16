# Setup a new project for a client organization

:::{warning}
This documentation is out of date.
We ended up deciding that we could not programmatically create projects.
This section will be removed, see [this issue for details](https://github.com/2i2c-org/org-ops/issues/4).
:::

Each client organization of 2i2c gets their own [GCP Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
This allows us to:

1. Maintain billing easily, since projects are the easiest unit of
   billing.
2. Give members of client organizations (such as IT teams) full access to
   the cloud project, without granting access to other client organizations'
   resources
3. Allow client organizations to take over running of the infrastructure
   themselves, with minimal disruption.

Client organizations can give us access to a billing account, or
just to a project. This document describes what 2i2c engineers should
do once client organizations give us access.

See {doc}`/howto/operate/new-cluster/azure-or-google-cloud` fore more detailed guidance.

## Client organization provides billing account

[Our pilot docs](https://pilot.2i2c.org/en/latest/admin/howto/create-billing-account.html#full-billing-account-access)
has information on how client organizations can provision a billing
account and give us access.

Once the client organization provides us with a billing account,
we provision a project for them inside the 2i2c.org GCP organization.
All this work happens in the [org-ops](https://github.com/2i2c-org/org-ops)
repository.

1. Edit `projects.tfvars`, adding an entry to `fully_managed_projects`.
   The key should be the name of the project we want to create, and the
   value should be the billing account ID. Add a comment referencing more
   information about the client organization, ideally pointing to a GitHub
   issue.

2. Make a commit, and create a pull request in the org-ops repository.

3. Run `terraform plan -var-file project.tfvars` to give you a detailed plan on
   what exactly terraform will do. Paste this in the PR description, and ask
   someone else for review.

4. Someone else should review the plan, and merge the PR. There should be co-ordination
   on when this is merged, so immediately after either the PR creator or merger
   can run `terraform apply -var-file projects.tfvars` after merging. They should
   make sure the diff isn't that different, and comment on the PR once it's done.

5. Validate that the project has been created, and you have access to it with
   your user account.

## Without billing account access

Sometimes, we won't have access to the billing account - the project would
be pre-created for us by the client organization. Our pilot docs have
information on [how client organizations can give us access](https://pilot.2i2c.org/en/latest/admin/howto/create-billing-account.html#project-level-access)

If these projects can *not* be moved into the 2i2c.org GCP organization,
we [can not](https://cloud.google.com/resource-manager/reference/rest/v1/projects/setIamPolicy)
automatically add 2i2c engineers as owners on the project. They will
need to be added manually via the [GCP Console web interface](https://console.cloud.google.com).
They will get an invite in their mail, which they must manually accept.

1. Find current list of 2i2c engineers who should have access to this GCP project,
   maintained in `variables.tf` under `project_owners` in the [org-ops](https://github.com/2i2c-org/org-ops),
   repository.

2. Use the GCP console to [invite all these users](https://cloud.google.com/iam/docs/granting-changing-revoking-access)
   to the project, giving them `Basic -> Owner` permissions. Make sure you
   are doing this in the correct GCP project!

3. Ping all those 2i2c engineers to make sure they accept the invite.

In the future, we should support:

1. Moving projects into 2i2c.org GCP organization when possible.
2. Decommission access to GCP projects when 2i2c engineers leave.
3. Make sure new 2i2c engineers are added to all projects we have access to.
