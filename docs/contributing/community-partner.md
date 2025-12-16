(infrastructure:review:community-partner)=
# Self-merging as a community partner

As part of our [shared responsibility model](https://docs.2i2c.org/en/latest/about/service/shared-responsibility.html), we may grant merge rights to partner engineers.
This allows others to merge changes that impact their community's infrastructure without requiring intervention from a 2i2c engineer.

Merge rights are only given for partners with which we have built a relationship of trust, on a case-by-case basis.
2i2c ultimately retains responsibility for the configuration of this infrastructure and its configuration.

[See the `2i2c-org/collaborators` team](https://github.com/orgs/2i2c-org/teams/collaborators) for a list of sub-teams and individuals with write access to this repository.

## Guidelines for community partners

Our goal is to provide trusted communities the ability to more quickly make changes to their infrastructure in order to lead to a better, more collaborative service for their community.
However, merge rights are a big responsibility, so please be careful in your actions.

Community partners *may* self-merge if they want to, provided the following conditions are met:

1. **They are confident debugging any issues that arise from the self-merged PR**.
   If any issues arise from your self-merge, **you are responsible for resolving them, or reverting the change**.
   You should understand the potential repurcussions of your change, and be ready to fix things if they break.
2. **They have access to their cloud cluster to debug changes**.
   Sometimes an issue requires intervention directly in the cloud infrastructure.
   Before self-merging, ensure that you are authorized and have login-access to this infrastructure.
3. **The change *only* touches files inside the `config/clusters/<cluster-name>` directory for their cluster.**
   Do not change configuration or code outside of your community's cluster folder without a review from a 2i2c engineer.
4. **The change is fairly standard, and not a novel configuration**.
   If something is straightforward (e.g., updating an environment image tag), then go for it.
   If you aren't quite sure what a change will impact, or you think you're doing something non-standard, ask for some help first.

   This is hard to quantify, but here are some examples of *routine* changes:

   - Adding a new hub that looks exactly like other hubs in the cluster
   - Changing resources provided to the hub
   - Adding / removing admin users
   - Changing profile options available to the hub

   Here are some examples of *novel* configuration that requires approval from a 2i2c engineer before merging:

   - Adding python code to `hub.extraConfig` to enable new functionality, such as
     adding a postgres database to each user pod.
   - Significant alterations to the configuration of the user pod, such as setting
     `singleuser.extraContainers`.
   - Modifications to how NFS home directory storage is managed.

As a general rule, when in doubt, ask for review :)

```{note}
These policies assume trust and good faith from the individuals to which we grant write-access.
We recognize that this will not scale as the communities we work with grows.
In the future, we plan to make **technical** restrictions on which folders a user may write to.
```

## Community hosted terraform state

In some cases, we want our community partners to be able to apply terraform changes
themselves too. You need to not only merge the pull request, but run `terraform apply`
appropriately for the change too. The general process for this is:

1. Make the PR
2. Run `terraform plan`, look at the output of changes that are going to be made *carefully*
3. Run `terraform apply`, make sure it succeeds
4. If `terraform apply` fails, work on the PR until it succeeds
5. Report on the PR that this change has been applied, and merge the PR

Since this requires access to [terraform state](https://developer.hashicorp.com/terraform/language/state),
running `terraform apply` is only possible if your community's terraform state is held separately,
and in a place you have access to. We don't do this for *all* communities, but we are able
to provide it for specific communities as needed.

*If* your community's terraform state is in its own bucket and you have access, you can
apply terraform changes with the following steps.

1. In your local checkout of the `2i2c-org/infrastructure` repository, `cd` into the
   appropriate directory under `terraform` for your cloud provider. `terraform/gcp` for
   Google Cloud, `terraform/aws` for AWS, `terraform/azure` for Azure and `terraform/openstack`
   for Jetstream2.

2. Make sure you're *authenticated* to be able to access the bucket containing state. This
   differs based on the provider, and here are some links to help: [GCP](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment), [AWS](https://docs.aws.amazon.com/cli/v1/userguide/cli-authentication-user.html), [Azure](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest)

3. Initialize the backend with `terraform init -backend-config=backends/<community-name>.hcl -reconfigure`,
   passing in the right community name in the `backends` directory. If there isn't a file
   there, it means your community doesn't have its own separate state and you can't do this.
   Reach out to us if this is the case.

4. Look at the list of [terraform workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces)
   with `terraform workspace list`. There should be an unused `default` workspace, and
   one workspace with your community's name.

5. Select the correct workspace with `terraform workspace select <community-name>`.

6. Run `terraform plan` with `terraform plan -var-file=projects/<community-name>.tfvars`.
   This evaluates your terraform changes, and tells you what changes are going to occur.
   Read these, and make sure you understand what is going on. While we have protections in
   place to prevent destructive changes, it's still possible for things to go bad. So,
   be careful!

   ```{warning}
   Like, be careful!
   ```

7. Once you're happy with the changes, run `terraform apply` with `terraform apply -var-file=projects/<community-name>.tfvars`.
   This will show you the output of `terraform plan` again. If that still looks good (in the
   rare case that someone else had changed the infrastructure in the time since you ran `terraform plan`),
   answer `yes`.

8. This should apply the changes you have. Watch the messages to make sure you're aware of
   the changes being made.

9. Add a note to the PR saying you have successfully applied this change, and merge the PR!