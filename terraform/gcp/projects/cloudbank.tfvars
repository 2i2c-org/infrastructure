# The state for this is stored in backend configured via backends/cloudbank.hcl
prefix     = "cb"
project_id = "cb-1003-1696"

zone             = "us-central1-b"
region           = "us-central1"
regional_cluster = false

enable_filestore_backups = false
filestores               = {}
single_process_oom_kill  = false

persistent_disks = {
  "authoring" = {
    size        = 25
    name_suffix = "authoring"
  }
  "bcc" = {
    size        = 60
    name_suffix = "bcc"
  }
  "berea" = {
    size        = 25
    name_suffix = "berea"
  }
  "bmcc" = {
    size        = 25
    name_suffix = "bmcc"
  }
  "boise" = {
    size        = 25
    name_suffix = "boise"
  }
  "carrollu" = {
    size        = 25
    name_suffix = "carrollu"
  }
  "cau" = {
    size        = 25
    name_suffix = "cau"
  }
  "ccsf" = {
    size        = 513
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
  "chicagostate" = {
    size        = 25
    name_suffix = "chicagostate"
  }
  "clarku" = {
    size        = 25
    name_suffix = "clarku"
  }
  "cloud-county" = {
    size        = 25
    name_suffix = "cloud-county"
  }
  "cmu" = {
    size        = 25
    name_suffix = "cmu"
  }
  "cra" = {
    size        = 25
    name_suffix = "cra"
  }
  "csm" = {
    size        = 150
    name_suffix = "csm"
  }
  "deanza" = {
    size        = 60
    name_suffix = "deanza"
  }
  "demo" = {
    size        = 35
    name_suffix = "demo"
  }
  "elac" = {
    size        = 40
    name_suffix = "elac"
  }
  "elcamino" = {
    size        = 350
    name_suffix = "elcamino"
  }
  "emich" = {
    size        = 25
    name_suffix = "emich"
  }
  "epcc" = {
    size        = 25
    name_suffix = "epcc"
  }
  "evc" = {
    size        = 200
    name_suffix = "evc"
  }
  "etsu" = {
    size        = 100
    name_suffix = "etsu"
  }
  "foothill" = {
    size        = 200
    name_suffix = "foothill"
  }
  "fresno" = {
    size        = 60
    name_suffix = "fresno"
  }
  "fullertoncc" = {
    size        = 25
    name_suffix = "fullertoncc"
  }
  "georgetown" = {
    size        = 25
    name_suffix = "georgetown"
  }
  "glendale" = {
    size        = 60
    name_suffix = "glendale"
  }
  "golden" = {
    size        = 25
    name_suffix = "golden"
  }
  "gpu-demo" = {
    size        = 500
    name_suffix = "gpu-demo"
  }
  "gssm" = {
    size        = 25
    name_suffix = "gssm"
  }
  "gwu" = {
    size        = 300
    name_suffix = "gwu"
  }
  "high" = {
    size        = 120
    name_suffix = "high"
  }
  "hmc" = {
    size        = 25
    name_suffix = "hmc"
  }
  "humboldt" = {
    size        = 200
    name_suffix = "humboldt"
  }
  "iit" = {
    size        = 25
    name_suffix = "iit"
  }
  "ivytech" = {
    size        = 25
    name_suffix = "ivytech"
  }
  "kean" = {
    size        = 25
    name_suffix = "kean"
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
  "mmc" = {
    size        = 25
    name_suffix = "mmc"
  }
  "miracosta" = {
    size        = 60
    name_suffix = "miracosta"
  }
  "mission" = {
    size        = 25
    name_suffix = "mission"
  }
  "monmouth" = {
    size        = 100
    name_suffix = "monmouth"
  }
  "moreno" = {
    size        = 60
    name_suffix = "moreno"
  }
  "nicc" = {
    size        = 25
    name_suffix = "nicc"
  }
  "norco" = {
    size        = 40
    name_suffix = "norco"
  }
  "nova" = {
    size        = 25
    name_suffix = "nova"
  }
  "ocu" = {
    size        = 25
    name_suffix = "ocu"
  }
  "oit" = {
    size        = 25
    name_suffix = "oit"
  }
  "orangecoast" = {
    size        = 25
    name_suffix = "orangecoast"
  }
  "ornl" = {
    size        = 25
    name_suffix = "ornl"
  }
  "palomar" = {
    size        = 40
    name_suffix = "palomar"
  }
  "pasadena" = {
    size        = 140
    name_suffix = "pasadena"
  }
  "psu" = {
    size        = 25
    name_suffix = "psu"
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
  "santiago" = {
    size        = 20
    name_suffix = "santiago"
  }
  "saddleback" = {
    size        = 60
    name_suffix = "saddleback"
  }
  "sbcc" = {
    size        = 100
    name_suffix = "sbcc"
  }
  "shasta" = {
    size        = 25
    name_suffix = "shasta"
  }
  "sierra" = {
    size        = 20
    name_suffix = "sierra"
  }
  "sjcc" = {
    size        = 30
    name_suffix = "sjcc"
  }
  "skyline" = {
    size        = 115
    name_suffix = "skyline"
  }
  "smc" = {
    size        = 25
    name_suffix = "smc"
  }
  "sou" = {
    size        = 100
    name_suffix = "sou"
  }
  "spelman" = {
    size        = 25
    name_suffix = "spelman"
  }
  "srjc" = {
    size        = 100
    name_suffix = "srjc"
  }
  "staging" = {
    size        = 2
    name_suffix = "staging"
  }
  "tiffin" = {
    size        = 25
    name_suffix = "tiffin"
  }
  "tntech" = {
    size        = 100
    name_suffix = "tntech"
  }
  "toledo" = {
    size        = 25
    name_suffix = "toledo"
  }
  "tuskegee" = {
    size        = 20
    name_suffix = "tuskegee"
  }
  "uams" = {
    size        = 25
    name_suffix = "uams"
  }
  "umd" = {
    size        = 50
    name_suffix = "umd"
  }
  "unc-chapel-hill" = {
    size        = 25
    name_suffix = "unc-chapel-hill"
  }
  "uncw" = {
    size        = 25
    name_suffix = "uncw"
  }
  "und" = {
    size        = 25
    name_suffix = "und"
  }
  "unr" = {
    size        = 40
    name_suffix = "unr"
  }
  "utpb" = {
    size        = 25
    name_suffix = "utpb"
  }
  "uwyo" = {
    size        = 25
    name_suffix = "uwyo"
  }
  "virginia" = {
    size        = 180
    name_suffix = "virginia"
  }
  "wcu" = {
    size        = 25
    name_suffix = "wcu"
  }
  "weber" = {
    size        = 25
    name_suffix = "weber"
  }
  "whitman" = {
    size        = 25
    name_suffix = "whitman"
  }
  "willamette" = {
    size        = 25
    name_suffix = "willamette"
  }
  "wlac" = {
    size        = 20
    name_suffix = "wlac"
  }
  "york" = {
    size        = 25
    name_suffix = "york"
  }
}

# Cloud costs for this project are not passed through by 2i2c
budget_alert_enabled = false
billing_account_id   = ""

k8s_versions = {
  # NOTE: This isn't a regional cluster / highly available cluster, when
  #       upgrading the control plane, there will be ~5 minutes of k8s not being
  #       available making new server launches error etc.
  min_master_version : "1.35.3-gke.1943000",
  core_nodes_version : "1.35.3-gke.1943000",
  notebook_nodes_version : "1.35.3-gke.1943000",
  dask_nodes_version : "1.35.3-gke.1943000",
}

core_node_machine_type = "n2-highmem-2"
# FIXME: this number should be updated, it was bumped to 30
#        in order to reflect an imperative change made to the infra
core_node_max_count   = 40
enable_network_policy = true

notebook_nodes = {
  "n2-highmem-4-b" : {
    min : 0,
    max : 100,
    machine_type : "n2-highmem-4",
    disk_size_gb : 150,
    node_version : "1.34.4-gke.1193000",
    taints : [
      # Prevent new pods from scheduling here.
      {
        key : "manual-phaseout"
        value : "noop"
        effect : "NO_SCHEDULE"
      }
    ],
  },
  "n2-highmem-4-a" : {
    min : 2,
    max : 100,
    machine_type : "n2-highmem-4",
    disk_size_gb : 150,
  },
  "gpu-t4" : {
    min : 0,
    max : 30,
    machine_type : "n1-highmem-8",
    disk_size_gb : 200,
    gpu : {
      enabled : true,
      type : "nvidia-tesla-t4",
      count : 1,
      share_gpu : true,
      sharing_strategy : "TIME_SHARING",
      shared_clients_per_gpu : 2
    },
    # Let's try a faster disk to see if that speeds up image pulls
    disk_type : "pd-ssd",
    zones : [
      # Get GPUs wherever they are available, as sometimes a single
      # zone might be out of GPUs.
      "us-central1-a",
      "us-central1-b",
      "us-central1-c",
      "us-central1-f"
    ]
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
