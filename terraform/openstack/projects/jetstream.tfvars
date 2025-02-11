prefix = "js"

notebook_nodes = {
  "m3.small" : {
    min : 1,
    max : 100,
    machine_type : "m3.small",
    labels = {
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }
  },
  "m3.tiny" : {
    min : 1,
    max : 100,
    machine_type : "m3.small",
    labels = {
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }
  },
}