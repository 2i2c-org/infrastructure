billing_account_id = "0157F7-E3EA8C-25AC3C"
budget_alert_amount = "500"

prefix                 = "two-eye-two-see-uk"
project_id             = "two-eye-two-see-uk"

zone                   = "europe-west2-b"
region                 = "europe-west2"

core_node_machine_type = "n1-highmem-4"
enable_network_policy  = true

# Setup a filestore for in-cluster NFS
enable_filestore       = true
filestore_capacity_gb  = 1024

# No plans to provide storage buckets to users on this hub, so no need to deploy config connector
config_connector_enabled = false

notebook_nodes = {
  "user" : {
    min : 0,
    max : 20,
    machine_type : "n1-highmem-4",
    labels: {},
    gpu: {
      enabled: false,
      type: "",
      count: 0
    }
  },
}

user_buckets = {}
