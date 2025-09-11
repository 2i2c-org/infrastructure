prefix     = "cb"
project_id = "cb-1003-1696"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

enable_filestore_backups = true
filestores = {
  "filestore" : { "capacity_gb" : 1792 }
}

persistent_disks = {
  "authoring" = {
    size        = 25
    name_suffix = "authoring"
  }
  "bcc" = {
    size        = 60
    name_suffix = "bcc"
  }
  "ccsf" = {
    size        = 450
    name_suffix = "ccsf"
  }
  "chabot" = {
    size        = 60
    name_suffix = "chabot"
  }
  "chaffey" = {
    size        = 25
    name_suffix = "chaffey"
  }
  "csm" = {
    size        = 150
    name_suffix = "csm"
  }
  "csum" = {
    size        = 25
    name_suffix = "csum"
  }
  "deanza" = {
    size        = 60
    name_suffix = "deanza"
  }
  "demo" = {
    size        = 35
    name_suffix = "demo"
  }
  "dvc" = {
    size        = 90
    name_suffix = "dvc"
  }
  "elac" = {
    size        = 40
    name_suffix = "elac"
  }
  "elcamino" = {
    size        = 350
    name_suffix = "elcamino"
  }
  "evc" = {
    size        = 200
    name_suffix = "evc"
  }
  "foothill" = {
    size        = 200
    name_suffix = "foothill"
  }
  "fresno" = {
    size        = 60
    name_suffix = "fresno"
  }
  "glendale" = {
    size        = 60
    name_suffix = "glendale"
  }
  "golden" = {
    size        = 25
    name_suffix = "golden"
  }
  "high" = {
    size        = 120
    name_suffix = "high"
  }
  "humboldt" = {
    size        = 200
    name_suffix = "humboldt"
  }
  "lacc" = {
    size        = 140
    name_suffix = "lacc"
  }
  "lahc" = {
    size        = 25
    name_suffix = "lahc"
  }
  "laney" = {
    size        = 200
    name_suffix = "laney"
  }
  "lavc" = {
    size        = 25
    name_suffix = "lavc"
  }
  "lbcc" = {
    size        = 25
    name_suffix = "lbcc"
  }
  "mendocino" = {
    size        = 40
    name_suffix = "mendocino"
  }
  "merced" = {
    size        = 60
    name_suffix = "merced"
  }
  "merritt" = {
    size        = 25
    name_suffix = "merritt"
  }
  "miracosta" = {
    size        = 60
    name_suffix = "miracosta"
  }
  "mission" = {
    size        = 25
    name_suffix = "mission"
  }
  "moreno" = {
    size        = 60
    name_suffix = "moreno"
  }
  "norco" = {
    size        = 40
    name_suffix = "norco"
  }
  "palomar" = {
    size        = 40
    name_suffix = "palomar"
  }
  "pasadena" = {
    size        = 140
    name_suffix = "pasadena"
  }
  "redwoods" = {
    size        = 40
    name_suffix = "redwoods"
  }
  "reedley" = {
    size        = 40
    name_suffix = "reedley"
  }
  "riohondo" = {
    size        = 20
    name_suffix = "riohondo"
  }
  "saddleback" = {
    size        = 60
    name_suffix = "saddleback"
  }
  "sbcc" = {
    size        = 100
    name_suffix = "sbcc"
  }
  "sbcc-dev" = {
    size        = 20
    name_suffix = "sbcc-dev"
  }
  "sierra" = {
    size        = 20
    name_suffix = "sierra"
  }
  "sjcc" = {
    size        = 30
    name_suffix = "sjcc"
  }
  "sjsu" = {
    size        = 20
    name_suffix = "sjsu"
  }
  "skyline" = {
    size        = 80
    name_suffix = "skyline"
  }
  "srjc" = {
    size        = 30
    name_suffix = "srjc"
  }
  "staging" = {
    size        = 2
    name_suffix = "staging"
  }
  "tuskegee" = {
    size        = 20
    name_suffix = "tuskegee"
  }
  "ucsc" = {
    size        = 20
    name_suffix = "ucsc"
  }
  "unr" = {
    size        = 40
    name_suffix = "unr"
  }
  "wlac" = {
    size        = 20
    name_suffix = "wlac"
  }
}

# Cloud costs for this project are not passed through by 2i2c
budget_alert_enabled = false
billing_account_id   = ""

k8s_versions = {
  # NOTE: This isn't a regional cluster / highly available cluster, when
  #       upgrading the control plane, there will be ~5 minutes of k8s not being
  #       available making new server launches error etc.
  min_master_version : "1.32.1-gke.1357001",
  core_nodes_version : "1.32.1-gke.1357001",
  notebook_nodes_version : "1.32.1-gke.1357001",
  dask_nodes_version : "1.32.1-gke.1357001",
}

core_node_machine_type = "n2-highmem-2"
core_node_max_count    = 20
enable_network_policy  = true

notebook_nodes = {
  "n2-highmem-4-b" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
  },
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16",
  },
  "n2-highmem-64" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-64",
  },
}

# Setup a single node pool for dask workers.
#
# A not yet fully established policy is being developed about using a single
# node pool, see https://github.com/2i2c-org/infrastructure/issues/2687.
#
dask_nodes = {
  "n2-highmem-16" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-16"
  },
}

user_buckets = {}
