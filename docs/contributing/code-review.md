(infrastructure:review)=
# Review and merge guidelines

Much of our active infrastructure is configured and automatically updated via CI/CD pipelines.
This means that changes in this repository often immediately impact the infrastructure that we run.
As such, we follow team policies for review/merge that are more specific [than our general development merge policies](tc:development:merge-policy).

This document codifies our guidelines for doing code review and merging pull requests on active infrastructure (ie, anything in the `infrastructure/` codebase).

> A Foolish Consistency is the Hobgoblin of Little Minds
> 
> - PEP 8

## Changing active infrastructure in general

The following general policies apply to any change that will affect active infrastructure.
Policies specific to **Terraform** changes [are described below](infrastructure:review:terraform).

Here are some guidelines for merging and reviewing in this case:

- **The PR author must also merge the PR**. (REQUIRED)
  Because a PR is a reflection of a _deploy_, the author of the PR should also be the one that merges it, since only they know what infrastructure has actually been deployed.
- **Explicitly list a back-up if you must step away**. (REQUIRED)
  PR authors are responsible for the infrastructure changes that they make.
  You should generally only make a change to live infrastructure if you'll have the bandwidth to ensure it is fixed if something goes wrong.
  If for some reason you **must** step away, make it clear who else is responsible for shepherding the PR.
- **Be careful when changing config of a hub *during* an event**
  Sometimes, a hub config change needs to happen *immediately*, to help debug something
  or change behavior during a time sensitive event. Local deploys are ok to make sure that
  users see the benefit immediately and we aren't blocking the progress of the event. However,
  make sure you push a PR with the change *and merge it quickly* to make sure that the changes
  are persisted across future deploys. Self merging is acceptable here, although this general
  class of changes should be limited as much as possible.
  
## Self-merging as a 2i2c engineer

**Be careful when self-merging without review**.

Because changing active infrastructure is potentially confusing or
disruptive to users, be extra careful if you self-merge without a
review approval.  Consider whether your commit will cause a change
that might be destructive and ask if you _really_ need to merge now
or can wait for review.  That said, sometimes the only way to
understand the impact of a change is to merge and see how things go,
so use your best judgment!

Here is a list of things you can clearly, unambigously self merge without
any approval.

1. Updating admin users for a hub
2. Changing basic hub configuration such as the URL of its landing page image
3. Updating the user image of a hub.
4. Updating the max number of nodes for nodepools in a cluster
5. Emergency (eg exam, outage) related resource bumps
6. *Cleanly* reverting a change that failed CI
  
## Self-merging as a community partner

As part of our [shared responsibility model](https://docs.2i2c.org/en/latest/about/service/shared-responsibility.html), we may grant merge rights to partner engineers.
This allows others to merge changes that impact their community's infrastructure without requiring intervention from a 2i2c engineer.

Merge rights are only given for partners with which we have built a relationship of trust, on a case-by-case basis.
2i2c ultimately retains responsibility for the configuration of this infrastructure and its configuration.

[See the `2i2c-org/collaborators` team](https://github.com/orgs/2i2c-org/teams/collaborators) for a list of sub-teams and individuals with write access to this repository.

### Guidelines for community partners

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

## Changing authentication related configuration

Extra caution must be taken when changing authentication related configuration. Since the current testing infrastructure doesn't automatically test the authentication workflow, any issue within the authentication process might go undetected and cause an outage, if no manual testing is conducted before deploying it to all the hubs.

To deploy changes to the authentication workflow, follow these steps:
1. **Propose changes**. Change the codebase and open a PR.
1. **Manually deploy changes to a few kinds of staging hubs**. The hubs use different authentication mechanisms, based on their needs, but testing on the staging hubs listed below should cover all the possible types. The hubs are:
   - cluster: `leap`, hub: `staging` (GitHub)
   - cluster: `utoronto`, hub: `staging` (Azure AD)
   - cluster: `2i2c`, hub: `staging` (CILogon)
1. **Login into the staging hubs**. Try logging in into the hubs where you deployed your changes.
1. **Start a server**. Afer you've logged into the hub, make sure everything works as expected by spinning up a server.
1. **Post the status of the manual steps above**. In your PR's top comment, post the hubs where you've deployed the changes and whether or not they are functioning properly.
1. **Wait for review and approval**. Leave the PR open for other team members to review and approve.

   :::{admonition} Guidelines for reviewing changes to authentication infrastructure
   :class: tip
   Apply slightly higher code review scrutiny when reviewing changes to the authentication workflow.
   :::
1. **Merge the change**. Once approved, merge the PR. This will deploy your change to all the hubs.

(infrastructure:review:terraform)=
## Terraform changes

[Terraform](tools:terraform) is used for directly provisioning and modifying cloud infrastructure (as opposed to just deploying applications on pre-existing cloud infrastructure).
This lets us treat our infrastructure as code, so we can use regular code quality practices (code review, linters, extensive documentation, etc) to keep the quality of our infrastructure high.
However, it comes with a few caveats:

1. Locally and iteratively testing terraform is impossible - as we
   develop it, the infrastructure is deployed / modified / destroyed
   as we go.
2. Behavior of terraform code differs based on the current
   state of the infrastructure (as represented in the
   [state file](https://www.terraform.io/docs/language/state/index.html)).
3. While `terraform plan` can tell us what terraform *thinks* it is
   going to do, it might not always succeed. Permission errors or
   organizational restrictions can cause it to fail. Timeouts can happen.
   Runtime errors pop up.

Thanks to all these, it is impossible to either:

- Accurately gauge the impact of a terraform code change just from looking at the text
- Automatically deploy it via continuous deployment

As a result, we have some workflows that are specific to using Terraform, described below.

### Changes to running infrastructure

In this scenario, there is already-running infrastructure and you are deploying changes to it.

To deploy changes, follow these steps:

1. **Propose changes**. Change the codebase and open a PR. **Do not deploy changes yet**. Use `terraform plan` rather than `terraform apply` do understand the change before deploying it.
1. **Post the output of `terraform plan`**. In your PR's top comment, post the output of `terraform plan` whenever you update the PR. This helps others review the likely impact on our infrastructure.
1. **Wait for review and approval**. Leave the PR open for other team members to review and approve.

   :::{admonition} Guidelines for reviewing changes to existing infrastructure
   :class: tip
   Focus is on both making sure the change is minimally disruptive, and on the quality of the infrastructure design.
   :::
1. **Deploy the change**. Once approved, leave a comment in the PR that you will start deploying the changes. Then `terraform apply` your change and verify it works ok.
1. **Iterate as needed**. If things break or you need to iterate on the deployment, follow this cycle until the infrastructure is in the state you wish:

   1. Amend your PR with changes
   2. Deploy with `terraform apply`
   3. Comment that you've made a deployment
1. **Communicate that you've finished deploying**. Leave a comment in the PR that the changes have been deployed. You should always communicate when a deploy has been made!
1. **Self-merge or request another review**. If you didn't need to make a change to the PR, merge the PR. If you made changes to the PR, use your judgement to decide if you should request another review or if you should self-merge it directly. If you merge, just leave a comment about changes made since the initial approval.


### Changes to set up new infrastructure

For creating *new* infrastructure, you are less-likely to deploy something disruptive to users, and you have a bit more flexibility to experiment.

The suggested workflow for setting up new infrastructure is:

1. **Iterate deploys locally**. Iteratively develop the code locally, testing it with `terraform apply` as you go.
2. **Start a PR early, and solicit feedback**. The primary goal here is to
   do a review of the *infrastructure design*, rather than of any particular
   `terraform plan` output.

   :::{admonition} Guidelines for reviewing changes to existing infrastructure
   :class: tip
   Focus of code review is just on infrastructure design.
   :::

3. **After approval, re-deploy from scratch**. Once someone else approves your PR, you should re-deploy the infrastructure from scratch to make sure that it exactly matches the PR's code. Do the following:

   1. Destroy the current infra you have setup with `terraform destroy`
   2. `terraform apply` from scratch.
   3. If things break, amend your PR until it unbreaks. This might solicit adding another cycle of code review.
   4. Self-merge the PR once the infra works as you would like.

   This way, terraform code will have been 'realized' by the time it is
   merged.

