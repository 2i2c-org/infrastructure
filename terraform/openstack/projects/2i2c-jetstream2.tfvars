prefix = "two-eye-two-see"

notebook_nodes = {
  "m3.quad" : {
    min : 1,
    max : 100,
    # 4 CPU, 15 RAM
    # https://docs.jetstream-cloud.org/general/instance-flavors/#jetstream2-cpu
    machine_type : "m3.quad",
    # We list the required labels here but unfortunately they have no effect
    # because of a bug in the Magnum CAPI driver
    labels = {
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }
  },
}

persistent_disks = {
  "staging" = {
    size        = 100 # in GB
    name_suffix = "staging"
    tags        = { "2i2c:hub-name" : "staging" }
  }
}