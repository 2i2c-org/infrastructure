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
                validation_message: "Must be an image location, matching ^.+:.+$"
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
