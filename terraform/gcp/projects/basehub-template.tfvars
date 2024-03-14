/*
 Some of the assumptions this template makes about the cluster:
   - multi-tenant with staging & prod hubs
   - regional
   - no scratch buckets support
*/

prefix     = "{{ cluster_name }}"
project_id = "{{ project_id }}"

zone   = "{{ cluster_region }}"
region = "{{ cluster_region }}"

# Default to a HA cluster for reliability
regional_cluster = true


# TODO: Before applying this, identify a k8s version to specify. Pick the latest
#       k8s version from GKE's regular release channel. Look at the output
#       called `regular_channel_latest_k8s_versions` as seen when using
#       `terraform plan -var-file=projects/{{ cluster_name }}.tfvars`.
#
#       Then use that version to explicitly set all k8s versions below, and
#       finally decomment the k8s_versions section and removing this comment.
#
#k8s_versions = {
#  min_master_version : "",
#  core_nodes_version : "",
#  notebook_nodes_version : "",
#}

core_node_machine_type = "n2-highmem-2"

# For multi-tenant cluster, network policy is required to enforce separation between hubs
enable_network_policy = true

# Setup a filestore for in-cluster NFS
enable_filestore      = true
filestore_capacity_gb = 1024

notebook_nodes = {
  "n2-highmem-4" : {
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
  }
}

user_buckets = {}
