(infrastructure:review)=
# Review and merge guidelines

## Mindset

This repository is *not* an open source *project* (unlike, for example,
[jupyterhub/jupyterhub](https://github.com/jupyterhub/jupyterhub)). It
is instead the *source of truth* for the infrastructure that 2i2c runs.
As such, it needs a different mindset on what review is **useful**.

When you merge a PR in an open source *project*, usually you have to keep
in mind a lot of factors:

1. How will this affect downstream users?
2. How will this affect me (and other maintainers) in the future as we
   try to change this?
3. How will this affect the direction of the project?

However, when we merge a PR in this *infrastructure repository*, the
factors are quite different:

1. What change will this actually make to our running infrastructure?
2. How do I know it has done the thing I intended it to do?
3. How do we mitigate the chance that we break something unintentionally?

This repository has **no downstream users**, which gives us a fair bit
of flexibility in how we go about it (subject only to restrictions based
on [Right to Replicate](https://2i2c.org/right-to-replicate/)).


## Prime directive

The following should be the prime directive under which we approach
making changes to this repository:

> Better to always move forward in the direction of the iteration / team
> goal, than to not.

It's a bias towards action, with the goal of empowering team members
to make progress, learn, break things (safely) and iterate as needed.

As a corollary, the primary role of **code review** is to **help
engineers grow** and build a coherent, high performance team that we can
all trust in, rather than a specific focus on 'the right thing'.

## Merging as a 2i2c engineer

After you make your PR, ask yourself these three questions:

1. *If* this PR breaks something, do you feel comfortable debugging it or
   reverting it to undo the change?
2. Do you know how to *verify* the effects of merging this PR?
3. Is this PR in service of moving forward on a task that you picked up
   from the Engineering Board?

If the answer to all these 3 questions are 'yes', you should go ahead
and self merge.

If it breaks, you can revert your PR, make changes, and try again.

Let's now explore the cases when answers to any of these questions are "no".

### I don't feel comfortable debugging this if it breaks

Congratulations, you have unearthed a (possibly scary) opportunity for growing
as an engineer!

A very important component of improving as an engineer is to be in the
following loop:

1. Make a change that breaks
2. Feel uncomfortable (required), and question your life choices that have led
   you to this moment (optional)
3. Remember that you are not an imposter, and while you may not have the
   specific **knowledge** about the issue, you have the **skills** to
   acquire this knowledge and fix the issue.
4. Boldly proceed into this uncertainity, and fix the issue, asking for
   and receiving help from the team as needed. See section below on
   [how to ask for help](contributing:code-review:help).

Note: You can also ask for help *before*.

As a **team**, our goal is to find ways to empower you to feel more
comfortable with things breaking, because you believe you can fix them
when they *do* break.
<a title="Reedy, CC BY-SA 4.0 &lt;https://creativecommons.org/licenses/by-sa/4.0&gt;, via Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT!%22_T-shirt.jpg"><img width="512" alt="Framed &quot;I BROKE WIKIPEDIA... THEN I FIXED IT!&quot; T-shirt" src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT%21%22_T-shirt.jpg/512px-Framed_%22I_BROKE_WIKIPEDIA..._THEN_I_FIXED_IT%21%22_T-shirt.jpg?20190318200628"></a>

We don't have a shirt like this, but maybe someday we could :)

### I don't know how to verify if what I did worked

Ask the community? I'm not sure what to say here

### This was not something picked up from the engineering board

Perils of unplanned work, and we should not do it.

This will make you uncomfortable, and that is ok. Sit in the discomfort!

How to handle 'little' quality of life improvement PRs? Like
https://github.com/2i2c-org/infrastructure/pull/4141?

(contributing:code-review:help)=
## How to ask for help?

1. Ask yourself - 'what about this change makes me uncomfortable?'. The
   primary goal of review / help should be to make you *more comfortable*
   so you can make the change, rather than to 'perfect' the code / config. Communicate what makes you uncomfortable, and use that to
   focus the review time.
2. Spend a *maximum* of 20min trying to think things through yourself
   before asking for help.


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
1. **Start a server**. After you've logged into the hub, make sure everything works as expected by spinning up a server.
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

