prefix = "binder-pythia"

image                   = "ubuntu-jammy-kube-v1.33.2-250626-0848"
capi_helm_chart_version = "0.16.0"

notebook_nodes = {
  "m3.large" : {
    min : 1,
    max : 100,
    # 16 CPU, 60 RAM
    # https://docs.jetstream-cloud.org/general/instance-flavors/#jetstream2-cpu
    machine_type : "m3.large",
    labels = {
      "hub.jupyter.org/node-purpose" = "user",
      "k8s.dask.org/node-purpose"    = "scheduler",
    }
  },
}
