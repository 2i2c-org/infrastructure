prefix     = "meom-ige"
project_id = "meom-ige-cnrs"

# Minimum number of nodes required to fit kube-system is either
# 2 n1-highcpu-2 nodes, or 3 g1-small nodes. If you don't enable
# networkpolicy, you can get away with 1 n1-custom-4-3840 node -
# but with that enable, calico-typha wants 2 replicas that
# must run on two nodes since they both want the same hostport.
# 3 g1-small is 13$ a month, wile a single n2-highcpu-2 is
# already 36$ a month. We want very low base price, and
# our core nodes will barely see any CPU usage, so g1-small is
# the way to go
core_node_machine_type = "g1-small"

# Single-tenant cluster, network policy not needed
enable_network_policy    = false

# Single tenant cluster, so bucket access is provided via
# metadata concealment + node SA. Config Connector not needed.
config_connector_enabled = false

notebook_nodes = {
  "small" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-2",
    labels: {}
  },
  "medium" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-8",
    labels: {}
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16",
    labels: {}
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32",
    labels: {}
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64",
    labels: {}
  },

}

dask_nodes = {
  "small" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-2",
    labels: {}
  },
  "medium" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-8",
    labels: {}
  },
  "large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-16",
    labels: {}
  },
  "very-large" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-32",
    labels: {}
  },
  "huge" : {
    min : 0,
    max : 20,
    machine_type : "n1-standard-64",
    labels: {}
  },

}

user_buckets = [
  "scratch",
  "data"
]
