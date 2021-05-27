prefix     = "meom"
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

# Give each user ~4G of RAM and ~2CPU
user_node_machine_type = "n1-custom-2-4096"
