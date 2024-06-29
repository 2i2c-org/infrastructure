(infrastructure:review:community-partner)=
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