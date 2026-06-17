{
  local profileList = import '../../../helm-charts/basehub/profile_lists_defaults/libsonnet/profileListsFunc.jsonnet',
  local r5xlarge_5 = import '../../../helm-charts/basehub/profile_lists_defaults/choices/r5.xlarge-5.json',
  local r54xlarge_2 = import '../../../helm-charts/basehub/profile_lists_defaults/choices/r5.4xlarge-2.json',

  local requestsChoices = profileList.makeChoiceDefault(r5xlarge_5 + r54xlarge_2, 'mem_2_gb'),

  local defaultProfileImageChoices = {
    python: {
      display_name: 'Py - NASA Openscapes Python, Dask Gateway 65d6916',
      slug: 'python',
      kubespawner_override: {
        image: 'openscapes/python:65d6916',
      },
    },
    pyrbase: {
      display_name: 'Py-R - py-rocket-base image 4.4-3.10',
      slug: 'pyrbase',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/py-rocket-base:latest',
      },
    },
    cryo: {
      display_name: 'Py - Cryointhecloud base image latest',
      slug: 'cryo',
      kubespawner_override: {
        image: 'quay.io/cryointhecloud/cryo-hub-image:latest',
      },
    },
    asar: {
      display_name: 'R - ASAR Stock Assessment',
      slug: 'asar',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/asar:latest',
      },
    },
    cefi: {
      display_name: 'Py-R - CEFI image latest',
      slug: 'cefi',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/cefi-image:latest',
      },
    },
    pyrgeo2: {
      display_name: 'Py-R - Geospatial + QGIS, Panoply, CWUtils - py-rocket-geospatial-2 latest',
      slug: 'pyrgeo2',
      default: true,
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/py-rocket-geospatial-2:latest',
      },
    },
    coastwatch: {
      display_name: 'Py-R - CoastWatch - coastwatch latest',
      slug: 'coastwatch',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/coastwatch:latest',
      },
    },
    aomlomics: {
      display_name: 'Py - Tourmaline Snakemake workflow for QIIME 2 v.2023.5',
      slug: 'aomlomics',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/aomlomics-jh:latest',
      },
    },
    iorocker: {
      display_name: 'R - Geospatial w sdmTMB - r-geospatial-sdm latest',
      slug: 'rgeospatialsdm',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/r-geospatial-sdm:latest',
      },
    },
    echopype: {
      display_name: 'Py - Echopype with pangeo - image-acoustics latest',
      slug: 'echopype',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/image-acoustics:latest',
      },
    },
    arcgis: {
      display_name: 'Py - ArcGIS Python 3.9',
      slug: 'arcgis',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/arcgis:latest',
      },
    },
    vast: {
      display_name: 'R - VAST with TMB - vast latest',
      kubespawner_override: {
        image: 'ghcr.io/nmfs-opensci/container-images/vast:latest',
      },
    },
    pace: {
      display_name: 'Py - PACE image with OCSSW tools',
      slug: 'pace',
      kubespawner_override: {
        image: 'quay.io/pacehackweek/pace-2024:latest',
      },
    },
  },

  local gpuProfileImageChoices = {
    pytorch: {
      display_name: 'Pangeo PyTorch ML Notebook',
      default: false,
      slug: 'pytorch',
      kubespawner_override: {
        image: 'quay.io/pangeo/pytorch-notebook:2024.11.11',
      },
    },
    tensorflow2: {
      display_name: 'Pangeo Tensorflow2 ML Notebook',
      default: true,
      slug: 'tensorflow2',
      kubespawner_override: {
        image: 'quay.io/pangeo/ml-notebook:2024.11.11',
      },
    },
  },

  local gpuKubespawnerOverride = {
    environment: {
      NVIDIA_DRIVER_CAPABILITIES: 'compute,utility',
    },
    mem_limit: null,
    mem_guarantee: '14G',
    node_selector: {
      'node.kubernetes.io/instance-type': 'g4dn.xlarge',
    },
    extra_resource_limits: {
      'nvidia.com/gpu': '1',
    },
  },

  getDefaultProfile:: profileList.makeProfile(
    profile_display='Default',
    dynamic_image_building_enabled=true,
    is_default_profile=true,
    image_choices=defaultProfileImageChoices,
    requests_choices=requestsChoices,
    unlisted_choice_enabled=true
  ),

  getGPUProfile:: profileList.makeProfile(
    profile_display='NVIDIA Tesla T4, ~16 GB, ~4 CPUs',
    profile_description='Start a container on a dedicated node with a GPU',
    dynamic_image_building_enabled=true,
    is_default_profile=false,
    image_choices=gpuProfileImageChoices,
    requests_choices={},
    unlisted_choice_enabled=true,
    profile_kubespawner_override=gpuKubespawnerOverride,
    profile_allowed_groups=[],
    slug='gpu'
  ),

}
