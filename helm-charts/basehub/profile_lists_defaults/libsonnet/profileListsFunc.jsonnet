{
  makeChoiceDefault(choice_dict, choice)::
    choice_dict {
      [choice]: choice_dict[choice] {
        default: true,
      },
    },

  makeProfile(
    profile_description='Choose image and resource allocation',
    profile_display,
    is_default_profile,
    slug='',
    unlisted_choice_enabled,
    profile_kubespawner_override={},
    profile_allowed_groups=[],
    image_display='Image',
    requests_display_name='Resource Allocation',
    dynamic_image_building_enabled,
    image_choices,
    requests_choices={},
  ):: {
    display_name: profile_display,
    description: profile_description,
    default: is_default_profile,
  } + if image_choices == {} && requests_choices == {} then {} else {
    profile_options: {
    } + if image_choices == {} then {} else {
      image: {
        display_name: image_display,
        dynamic_image_building: {
          enabled: dynamic_image_building_enabled,
        },
        choices: image_choices,
        unlisted_choice: {
          enabled: unlisted_choice_enabled,
          display_name: 'Custom image',
          validation_regex: '^.+:.+$',
          validation_message: 'Must be a publicly available docker image, of form <image-name>:<tag>',
          kubespawner_override: {
            image: '{value}',
          },
        },
      } + if requests_choices == {} then {} else {
        requests: {
          display_name: requests_display_name,
          choices: requests_choices,
        },
      },
    },
  } + if profile_kubespawner_override == {} then {} else {
    kubespawner_override: profile_kubespawner_override,
  } + if profile_allowed_groups == [] then {} else {
    profile_allowed_groups: profile_allowed_groups,
  } + if slug == '' then {} else {
    slug: slug,
  },
}
