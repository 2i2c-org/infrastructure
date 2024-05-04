(howto:features:unlisted-choice)=
# Allow users to setup custom, free-form user profile choices

Sometimes it is useful to allow users to specify their own, free-form choice for an option.
We can make this possible by enabling and configuring [`KubeSpawner.profile_list.<profile>.profile_options.<option>.unlisted_choice`](https://jupyterhub-kubespawner.readthedocs.io/en/latest/spawner.html#kubespawner.KubeSpawner.profile_list).

If enabled, when the user selects “Other” as a choice, a free form input is enabled. An optional regex can be configured that the free form input should match - eg. `^pangeo/.*$`.

Example configuration that allows a custom free-form, user specified image:

```yaml
jupyterhub:
   singleuser:
      profileList:
        - display_name: "CPU only"
          description: "Start a container limited to a chosen share of capacity on a node of this type"
          profile_options:
            image:
              display_name: Image
              unlisted_choice:
                enabled: True
                display_name: "Custom image"
                validation_regex: "^.+:.+$"
                validation_message: "Must be a publicly available docker image, of form <image-name>:<tag>"
                kubespawner_override:
                  image: "{value}"
              choices:
                pangeo_new:
                  display_name: Base Pangeo Notebook ("2023.05.18")
                  default: true
                  slug: "pangeo_new"
                  kubespawner_override:
                    image: "pangeo/pangeo-notebook:2023.05.18"
                pangeo_old: (...)
```

## Allow members of a particular github team only to test custom images

In some hubs, we don't want *everyone* to be able to specify an image - but
we do want some subset of users to be able to do so, for testing
purposes. This can be done by coupling `unlisted_choice` with
[`allowed_groups`](howto:features:profile-restrict).

In the `profileList` for the hub in question, add a profile like this:

```yaml
        - display_name: "Test custom image"
          description: Test any custom image before rolling it out to rest of your users
          slug: custom-image-only
          allowed_groups:
            - 2i2c-org:hub-access-for-2i2c-staff
            - <other-github-teams>
          profile_options:
            image:
              display_name: Image
              unlisted_choice:
                enabled: True
                display_name: "Custom image"
                validation_regex: "^.+:.+$"
                validation_message: "Must be a publicly available docker image, of form <image-name>:<tag>"
                kubespawner_override:
                  image: "{value}"
              choices: {}
```
