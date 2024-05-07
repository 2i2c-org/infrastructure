(howto:features:profile-restrict)=
# Restrict profile options based on JupyterHub groups (or GitHub teams)

```{warning}
This is currently only functional for GitHub authentication with `GitHubOAuthenticator`,
and the earthscope hub is special cased. This will be more generally available once
group management is [broadly available](https://github.com/jupyterhub/oauthenticator/pull/735)
on OAuthenticator.
```

Communities often want to *selectively* grant access to resources based on
what *groups* a user belongs to. The most common example being restricted
access to GPUs, really large resource allocations or the ability to specify
[arbitrary images to launch](howto:features:unlisted-choice).

We override the [`profile_list`](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html#kubespawner.KubeSpawner.profile_list)
feature of KubeSpawner to be able to restrict specific profiles or profile options
to only be available to users who belong to specific JupyterHub groups (or in the
case of using GitHub authentication, GitHub teams).

## The `allowed_groups` configuration

The key `allowed_groups` can be set under:

1. Any **Profile** - the first level of options shown in the profile selection screen
   to the user, selectable via radio buttons.
2. Any **Profile Option Choice** - the second level of options shown in the profile
   selection screen to the user, selectable via dropdown box.
3. Any **Profile Option Unlisted Choice** - the optional way for end users to write in
   an arbitrary value to be used, often for selecting the image to be run, instead of
   selecting one of the pre-determined values.

It can contain a list of JupyterHub **group names**. These are determined either via
the JupyterHub admin interface or provided externally via the authentication provider
(see below for how the group names look like)

If `allowed_groups` is not set, that profile, profile option choice or unlisted choice, will be visible and available to everyone who can log in to the hub/

So to restrict a profile, profile option choice or unlisted choice to a specific set
of users, put a `allowed_groups` config under whatever you want to restrict, and list
the groups that should be *allowed* access. Everyone else will not see that option,
and members of that group will.

Now let's look at some examples.

### Example 1: Restrict an entire profile

Let's say a community wants to restrict a Matlab profile only to a select few
users, but their python environment be available to everyone. And they are using GitHub as their
authentication provider, with `GitHubOAuthenticator`.

We would have a `profileList` like this:

```yaml
- display_name: Python
  description: Python datascience environment
  default: true
  kubespawner_override:
    image: python-image:tag
  profile_options: &profile_options
    requests: &profile_options_resource_allocation
      display_name: Resource Allocation
      choices:
        mem_1_9:
          display_name: 1.9 GB RAM, upto 3.7 CPUs
          kubespawner_override:
            mem_guarantee: 1991244775
            mem_limit: 1991244775
            cpu_guarantee: 0.2328125
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
          default: true
        mem_3_7:
          display_name: 3.7 GB RAM, upto 3.7 CPUs
          kubespawner_override:
            mem_guarantee: 3982489550
            mem_limit: 3982489550
            cpu_guarantee: 0.465625
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
        mem_7_4:
          display_name: 7.4 GB RAM, upto 3.7 CPUs
          kubespawner_override:
            mem_guarantee: 7964979101
            mem_limit: 7964979101
            cpu_guarantee: 0.93125
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
- display_name: Matlab
  description: Matlab environment
  allowed_groups:
    - 2i2c-org:hub-access-for-2i2c-staff
    - organization:matlab-access
  kubespawner_override:
    image: matlab-image:tag
  profile_options: *profile_options
```

The `Python` profile does not have an `allowed_groups` set, so everyone who can
log in to the hub can use that. The `Matlab` profile has an `allowed_groups` set,
and allows two groups - one specifically for 2i2c staff members, and another for
those the community has added to a `matlab-access` team inside their GitHub org.

### Example 2: Restrict a particular `profile_option` choice

Now let's say the community wants to restrict only users who are members of a
`large-compute` team to access the `7.4 GB RAM, upto 3.7 CPUs` and
`3.7 GB RAM, upto 3.7 CPUs` profile option.

```yaml
- display_name: Python
  description: Python datascience environment
  default: true
  kubespawner_override:
    image: python-image:tag
  profile_options: &profile_options
    requests: &profile_options_resource_allocation
      display_name: Resource Allocation
      choices:
        mem_1_9:
          display_name: 1.9 GB RAM, upto 3.7 CPUs
          kubespawner_override:
            mem_guarantee: 1991244775
            mem_limit: 1991244775
            cpu_guarantee: 0.2328125
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
          default: true
        mem_3_7:
          display_name: 3.7 GB RAM, upto 3.7 CPUs
          allowed_groups:
          - 2i2c-org:hub-access-for-2i2c-staff
          - organization:large-compute
          kubespawner_override:
            mem_guarantee: 3982489550
            mem_limit: 3982489550
            cpu_guarantee: 0.465625
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
        mem_7_4:
          display_name: 7.4 GB RAM, upto 3.7 CPUs
          allowed_groups:
          - 2i2c-org:hub-access-for-2i2c-staff
          - organization:large-compute
          kubespawner_override:
            mem_guarantee: 7964979101
            mem_limit: 7964979101
            cpu_guarantee: 0.93125
            cpu_limit: 3.725
            node_selector:
              node.kubernetes.io/instance-type: r5.xlarge
- display_name: Matlab
  description: Matlab environment
  allowed_groups:
    - 2i2c-org:hub-access-for-2i2c-staff
    - organization:matlab-access
  kubespawner_override:
    image: matlab-image:tag
  profile_options: *profile_options
```

Since this adds on from the previous example, it'll have the following behavior:

1. Everyone can see and use the Python profile
2. Only members of the team `matlab-access` (and 2i2c staff) can see the `Matlab`
   profile.
3. Only members of the team `large-compute` can see the two larger dropdown
   items. This `profile_option` is the same for both python and matlab, so this
   behavior is repeated for both of them.
4. So only people who are members of *both* `matlab-access` and `large-compute` can
   see the larger dropdown options for the Matlab profile.

## Enabling externally managed groups for `GitHubOAuthenticator`

For hubs using `GitHubOAuthenticator`, groups (for the purposes of this feature alone)
are of the form `<github-org-name>:<github-team-name>`.

The following extra config is also required to enable this feature.

```yaml
jupyterhub:
  hub:
    config:
      Authenticator:
        enable_auth_state: true
      GitHubOAuthenticator:
        populate_teams_in_auth_state: true
```

```{note}
GitHubOAuthenticator is currently special cased in our code, until
[this PR](https://github.com/jupyterhub/oauthenticator/pull/735) is merged
and deployed. `allowed_groups` will treat GitHub team membership as groups,
but other JupyterHub functionality that depends on groups will not.
```

### Enabling access for 2i2c engineers

All 2i2c engineers are part of the GitHub team `2i2c-org:hub-access-for-2i2c-staff`, so
every `allowed_group` entry should have an explicit mention of that team so 2i2c engineers
can access that option / profile and test it out when needed.

## Enabling this feature for other Authenticators

Currently, the EarthScope hub has this feature enabled via custom overrides. Once
[this PR](https://github.com/jupyterhub/oauthenticator/pull/735) is merged and
deployed, we can enable this feature for hubs using other Authenticators more generally.