prefix = "binder-pythia"

notebook_nodes = {
  "m3.medium" : {
    min : 1,
    max : 100,
    # 8 CPU,	30 RAM
    # https://docs.jetstream-cloud.org/general/instance-flavors/#jetstream2-cpu
    machine_type : "m3.medium",
    labels = {
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }
  },
}