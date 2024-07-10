variable "prefix" {
  type        = string
  description = <<-EOT
  Prefix for all objects created by terraform.

  Primary identifier to 'group' together resources created by
  this terraform module. Prevents clashes with other resources
  in the cloud project / account.

  Should not be changed after first terraform apply - doing so
  will recreate all resources.

  Should not end with a '-', that is automatically added.
  EOT
}

variable "project_id" {
  type        = string
  description = <<-EOT
  GCP Project ID to create resources in.

  Should be the id, rather than display name of the project.
  EOT
}

variable "billing_account_id" {
  type        = string
  description = <<-EOT
  ID of the billing account used for this project. Used to set up alerts
  for budget forecasts.
  EOT
}

variable "budget_alert_currency" {
  type        = string
  default     = "USD"
  description = <<-EOT
  Currency used for budget alerts.
  EOT
}

variable "budget_alert_amount" {
  type        = string
  description = <<-EOT
  Amount of *forecasted spend* at which to send a billing alert. Current practice
  is to set this to the average of the last 3 months expenditure + 20%.
  EOT
}

variable "budget_alert_enabled" {
  type        = bool
  default     = true
  description = <<-EOT
  Enable budget alerts. Disable in cases where we do not have enough permissions
  on the billing account or cloud account to enable APIs.
  EOT
}

variable "k8s_version_prefixes" {
  type = set(string)
  # Available minor versions are picked from the GKE regular release channel. To
  # see the available versions see
  # https://cloud.google.com/kubernetes-engine/docs/release-notes-regular
  #
  # This list should list all minor versions available in the regular release
  # channel, so we may want to remove or add minor versions here over time.
  #
  default = [
    "1.27.",
    "1.28.",
    "1.29.",
    "1.",
  ]
  description = <<-EOT
  A list of k8s version prefixes that can be evaluated to their latest version by
  the output defined in cluster.tf called regular_channel_latest_k8s_versions.

  For details about release channels (rapid, regular, stable), see:
  https://cloud.google.com/kubernetes-engine/docs/concepts/release-channels#channels
  EOT
}

variable "k8s_versions" {
  type = object({
    min_master_version : optional(string, null),
    core_nodes_version : optional(string, null),
    notebook_nodes_version : optional(string, null),
    dask_nodes_version : optional(string, null),
  })
  default     = {}
  description = <<-EOT
  Configuration of the k8s cluster's version and node pools' versions. To specify these

  - min_master_nodes is passthrough configuration of google_container_cluster's min_master_version, documented in https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster#min_master_version
  - [core|notebook|dask]_nodes_version is passthrough configuration of container_node_pool's version, documented in https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_node_pool#version
  EOT
}

variable "notebook_nodes" {
  type = map(object({
    min : number,
    max : number,
    machine_type : string,
    labels : optional(map(string), {}),
    taints : optional(list(object({
      key : string,
      value : string,
      effect : string
    })), [])
    # Balanced disks are much faster than standard disks, and much cheaper
    # than SSD disks. It contributes heavily to how fast new nodes spin up,
    # as images being pulled takes up a lot of new node spin up time.
    # Faster disks provide faster image pulls!
    disk_type : optional(string, "pd-balanced"),
    disk_size_gb : optional(number, 100),
    gpu : optional(
      object({
        enabled : optional(bool, false),
        type : optional(string, ""),
        count : optional(number, 1)
      }),
      {}
    ),
    resource_labels : optional(map(string), {}),
    zones : optional(list(string), []),
    node_version : optional(string, ""),
  }))
  description = "Notebook node pools to create"
  default     = {}
}

variable "dask_nodes" {
  type = map(object({
    min : number,
    max : number,
    preemptible : optional(bool, true),
    machine_type : string,
    labels : optional(map(string), {}),
    taints : optional(list(object({
      key : string,
      value : string,
      effect : string
    })), [])
    # Balanced disks are much faster than standard disks, and much cheaper
    # than SSD disks. It contributes heavily to how fast new nodes spin up,
    # as images being pulled takes up a lot of new node spin up time.
    # Faster disks provide faster image pulls!
    disk_type : optional(string, "pd-balanced"),
    disk_size_gb : optional(number, 100),
    gpu : optional(
      object({
        enabled : optional(bool, false),
        type : optional(string, ""),
        count : optional(number, 1)
      }),
      {}
    ),
    resource_labels : optional(map(string), {}),
    zones : optional(list(string), [])
    node_version : optional(string, ""),
  }))
  description = "Dask node pools to create. Defaults to notebook_nodes"
  default     = {}
}

variable "cd_sa_roles" {
  type = set(string)
  default = [
    "roles/container.admin",
    "roles/artifactregistry.writer"
  ]
  description = <<-EOT
  List of roles granted to the SA used by our CI/CD pipeline.

  We want to automatically build / push images, and deploy to
  the kubernetes cluster from CI/CD (on GitHub actions, mostly).
  A JSON key for this will be generated (with
  `terraform output -raw ci_deployer_key`) and stored in the
  repo in encrypted form.

  The default provides *full* access to the entire kubernetes
  cluster! This is dangerous, but it is unclear how to tamp
  it down.
  EOT
}

variable "region" {
  type        = string
  description = <<-EOT
  GCP Region the cluster & resources will be placed in.

  For research clusters, this should be closest to where
  your source data is.

  This does not imply that the cluster will be a regional
  cluster.
  EOT

}

variable "regional_cluster" {
  type        = bool
  default     = true
  description = <<-EOT
  Enable to have a highly available cluster with multi zonal masters

  These are more reliable, as otherwise the k8s API might have small
  outages now and then - with this set to false, the nodes serving
  the k8s API can go down periodically for upgrades.

  See https://cloud.google.com/kubernetes-engine/docs/concepts/regional-clusters
  for more information
  EOT
}


variable "zone" {
  type        = string
  description = <<-EOT
  GCP Zone the cluster & nodes will be set up in.

  Even with a regional cluster, all the cluster nodes will
  be on a single zone. NFS and supporting VMs will need to
  be in this zone as well.
  EOT
}

variable "core_node_machine_type" {
  type        = string
  description = <<-EOT
  Machine type to use for core nodes.

  Core nodes will always be on, and count as 'base cost'
  for a cluster. We should try to run with as few of them
  as possible.

  For single-tenant clusters, a single n2-highmem-2 node can be
  enough.
  EOT
}

variable "core_node_max_count" {
  type        = number
  default     = 5
  description = <<-EOT
  Maximum number of core nodes available.

  Core nodes can scale up to this many nodes if necessary.
  They are part of the 'base cost', should be kept to a minimum.
  This number should be small enough to prevent runaway scaling,
  but large enough to support occasional spikes for whatever reason.

  Minimum node count is fixed at 1.
  EOT
}

variable "enable_network_policy" {
  type        = bool
  default     = false
  description = <<-EOT
  Enable kubernetes network policy enforcement.

  Our z2jh deploys NetworkPolicies by default - but they are
  not enforced unless enforcement is turned on here. This takes
  up some cluster resources, so we could turn it off in cases
  where we are trying to minimize base cost.

  https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy
  has more information.
  EOT
}

variable "user_buckets" {
  type = map(object({
    delete_after : number,
    extra_admin_members : optional(list(string), []),
    public_access : optional(bool, false),
    usage_logs : optional(bool, false)
  }))
  default     = {}
  description = <<-EOT
  GCS Buckets to be created.

  The key for each entry will be prefixed with {var.prefix}- to form
  the name of the bucket.

  The value is a map, accepting the following keys:

  'delete_after' specifies the number of days after which any content
  in the bucket will be deleted. Set to null to not delete data.

  'extra_admin_members' describes extra identities (user groups, user accounts,
  service accounts, etc) that will have *full* access to this bucket. This
  is primarily useful for moving data into and out of buckets from outside
  the cloud. See https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_iam#member/members
  for the format this would be specified in.

  'public_access', if set to true, makes the bucket fully accessible to
  the public internet, without any authentication. This must be used with
  *extreme* care as it can explode network egress costs immensely, and
  should only be allowed on projects where 2i2c is *not* paying the cloud
  bill to be recouped later.

  'usage_logs', if set to true, will write GCS usage logs detailing
  access to objects in this GCS bucket. https://cloud.google.com/storage/docs/access-logs
  has more details. The bucket these will be written to can be determined by
  the `usage_logs_bucket` terraform output variable.
  EOT
}

variable "enable_private_cluster" {
  type        = bool
  default     = false
  description = <<-EOT
  Deploy the kubernetes cluster into a private subnet

  By default, GKE gives each of your nodes a public IP & puts them in a public
  subnet. When this variable is set to `true`, the nodes will be in a private subnet
  and not have public IPs. A cloud NAT will provide outbound internet access from
  these nodes. The kubernetes API will still be exposed publicly, so we can access
  it from our laptops & CD.

  This is often required by institutional controls banning VMs from having public IPs.
  EOT
}

variable "filestores" {
  type = map(object({
    name_suffix : optional(string, null),
    capacity_gb : optional(number, 1024),
    tier : optional(string, "BASIC_HDD"),
  }))
  default = {
    "filestore" : {}
  }
  description = <<-EOT
  Deploy one or more FileStores for home directories.

  This provisions a managed NFS solution that can be mounted as
  home directories for users. If this is not enabled, a manual or
  in-cluster NFS solution must be set up.

  - name-suffix: Suffix to append to the name of the FileStore. This
      prevents name-clashing. Default: null.
  - capacity_gb: Minimum size (in GB) of Google FileStore. Minimum
      is 1024 for BASIC_HDD tier, and 2560 for BASIC_SSD tier.
      Default: 1024.
  - tier: Google FileStore service tier to use. Most likely BASIC_HDD
      (for slower home directories, min $204 / month) or BASIC_SSD (for
      faster home directories, min $768 / month). Default: BASIC_HDD.
  EOT
}

variable "filestore_alert_available_percent" {
  type        = number
  default     = 10
  description = <<-EOT
  % of free space in filestore available under which to fire an alert to pagerduty.
  EOT
}


variable "enable_node_autoprovisioning" {
  type        = bool
  default     = false
  description = <<-EOT
  Enable auto-provisioning of nodes based on workload
  EOT
}

// Defaults for the below variables are taken from the original Pangeo cluster setup
// https://github.com/pangeo-data/pangeo-cloud-federation/blob/d051d1829aeb303d321dd483450146891f67a93c/deployments/gcp-uscentral1b/Makefile#L25
variable "min_memory" {
  type        = number
  default     = 1
  description = <<-EOT
  When auto-provisioning nodes, this is the minimum amount of memory the nodes
  should allocate in GB.

  Default = 1 GB
  EOT
}

variable "max_memory" {
  type        = number
  default     = 5200
  description = <<-EOT
  When auto-provisioning nodes, this is the minimum amount of memory the nodes
  should allocate in GB.

  Default = 5200 GB
  EOT
}

variable "min_cpu" {
  type        = number
  default     = 1
  description = <<-EOT
  When auto-provisioning nodes, this is the minimum number of cores in the
  cluster to which the cluster can scale.

  Default = 1 CPU
  EOT
}

variable "max_cpu" {
  type        = number
  default     = 1000
  description = <<-EOT
  When auto-provisioning nodes, this is the minimum number of cores in the
  cluster to which the cluster can scale.

  Default = 1000
  EOT
}

variable "hub_cloud_permissions" {
  type = map(
    object({
      allow_access_to_external_requester_pays_buckets : optional(bool, false),
      bucket_admin_access : set(string),
      bucket_readonly_access : optional(set(string), []),
      hub_namespace : string
    })
  )
  default     = {}
  description = <<-EOT
  Map of cloud permissions given to a particular hub

  Key is name of the hub namespace in the cluster, and values are particular
  permissions users running on those hubs should have. Currently supported are:

  1. allow_access_to_external_requester_pays_buckets: Allow code running in user servers from this
     hub to identify as coming from this particular GCP project when accessing GCS buckets in other projects
     marked as 'Requester Pays'. In this case, the egress costs will
     be borne by the project *containing the hub*, rather than the project *containing the bucket*.
     Egress costs can get quite expensive, so this is 'opt-in'.
  2. bucket_admin_access: List of GCS storage buckets that users on this hub should have read
     and write permissions for.
  EOT
}

variable "container_repos" {
  type        = list(any)
  default     = []
  description = <<-EOT
  A list of container repositories to create in Google Artifact Registry to store Docker
  images. Each entry is the name of the hub namespace in the cluster. If deploying a
  BinderHub, definitely add the namespace here so that there is somewhere to push the
  repo2docker-built images to.
  EOT
}

variable "enable_logging" {
  type        = bool
  default     = true
  description = <<-EOT
  Conditionally enable usage logs to be written to a bucket. This is generally a
  useful feature so is OPT-OUT.

  When true, a bucket for storing usage logs is created with the appropriate
  access policy.
  EOT
}
