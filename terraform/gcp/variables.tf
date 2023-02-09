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

variable "notebook_nodes" {
  type        = map(object({ min : number, max : number, machine_type : string, labels : map(string), gpu : object({ enabled : bool, type : string, count : number }) }))
  description = "Notebook node pools to create"
  default     = {}
}

variable "dask_nodes" {
  type        = map(object({ min : number, max : number, machine_type : string, labels : map(string), gpu : object({ enabled : bool, type : string, count : number }) }))
  description = "Dask node pools to create. Defaults to notebook_nodes"
  default     = {}
}

variable "config_connector_enabled" {
  type        = bool
  default     = false
  description = <<-EOT
  Enable GKE Config Connector to manage GCP resources via kubernetes.

  GKE Config Connector (https://cloud.google.com/config-connector/docs/overview)
  allows creating GCP resources (like buckets, VMs, etc) via creating Kubernetes
  Custom Resources. We use this to create buckets on a per-hub level,
  and could use it for other purposes in the future.

  Enabling this increases base cost, as config connector related pods
  needs to run on the cluster.
  EOT
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
  default     = "us-central1"
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
  default     = "us-central1-b"
  description = <<-EOT
  GCP Zone the cluster & nodes will be set up in.

  Even with a regional cluster, all the cluster nodes will
  be on a single zone. NFS and supporting VMs will need to
  be in this zone as well.
  EOT
}

variable "core_node_machine_type" {
  type        = string
  default     = "n1-highmem-2"
  description = <<-EOT
  Machine type to use for core nodes.

  Core nodes will always be on, and count as 'base cost'
  for a cluster. We should try to run with as few of them
  as possible.

  For single-tenant clusters, a single n1-highmem-2 node seems
  enough - if network policy and config connector are not on.
  For others, please experiment to see what fits.
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
  but large enough to support ocassional spikes for whatever reason.

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
  type        = map(object({ delete_after : number }))
  default     = {}
  description = <<-EOT
  GCS Buckets to be created.

  The key for each entry will be prefixed with {var.prefix}- to form
  the name of the bucket.

  The value is a map, with 'delete_after' the only accepted key in that
  map - it lists the number of days after which any content in the
  bucket will be deleted. Set to null to not delete data.
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

variable "enable_filestore" {
  type        = bool
  default     = false
  description = <<-EOT
  Deploy a Google FileStore for home directories

  This provisions a managed NFS solution that can be mounted as
  home directories for users. If this is not enabled, a manual or
  in-cluster NFS solution must be set up
  EOT
}

variable "filestore_capacity_gb" {
  type        = number
  default     = 1024
  description = <<-EOT
  Minimum size (in GB) of Google FileStore.

  Minimum is 1024 for BASIC_HDD tier, and 2560 for BASIC_SSD tier.
  EOT
}

variable "filestore_tier" {
  type        = string
  default     = "BASIC_HDD"
  description = <<-EOT
  Google FileStore service tier to use.

  Most likely BASIC_HDD (for slower home directories, min $204 / month) or
  BASIC_SSD (for faster home directories, min $768 / month)
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
  type        = map(object({ requestor_pays : bool, bucket_admin_access : set(string), hub_namespace : string }))
  default     = {}
  description = <<-EOT
  Map of cloud permissions given to a particular hub

  Key is name of the hub namespace in the cluster, and values are particular
  permissions users running on those hubs should have. Currently supported are:

  1. requestor_pays: Identify as coming from the google cloud project when accessing
     storage buckets marked as  https://cloud.google.com/storage/docs/requester-pays.
     This *potentially* incurs cost for us, the originating project, so opt-in.
  2. bucket_admin_access: List of GCS storage buckets that users on this hub should have read
     and write permissions for.
  EOT
}

variable "bucket_public_access" {
  type        = list
  default     = []
  description = <<-EOT
  A list of GCS storage buckets defined in user_buckets that should be granted public read access.

  EOT
}

variable "container_repos" {
  type        = list
  default     = []
  description = <<-EOT
  A list of container repositories to create in Google Artifact Registry to store Docker
  images. Each entry is the name of the hub namespace in the cluster. If deploying a
  BinderHub, definitely add the namespace here so that there is somewhere to push the
  repo2docker-built images to.
  EOT
}
