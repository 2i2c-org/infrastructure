// Cost monitoring resources for IAM role and cost allocation tags.
// Note: if the name of the IAM role is changed, then update the config in helm-charts/support/values.jsonnet for the k8s service account annotation.

# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
resource "aws_iam_role" "jupyterhub_cost_monitoring_iam_role" {
  count = var.enable_jupyterhub_cost_monitoring ? 1 : 0

  name = "jupyterhub_cost_monitoring_iam_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow",
      Action = "sts:AssumeRoleWithWebIdentity",
      Principal = {
        Federated = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}"
      },

      Condition = {
        StringEquals = {
          "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:support:jupyterhub-cost-monitoring"
        }
      },
    }]
  })
}

resource "aws_iam_role_policy" "jupyterhub_cost_monitoring_iam_policy" {
  count = var.enable_jupyterhub_cost_monitoring ? 1 : 0
  name  = "jupyterhub_cost_monitoring_iam_policy"
  role  = aws_iam_role.jupyterhub_cost_monitoring_iam_role[count.index].name
  # ref: https://docs.aws.amazon.com/service-authorization/latest/reference/list_awscostexplorerservice.html
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ce:Get*",
          "ce:List*",
        ],
        Resource = "*",
      },
    ]
  })
}

resource "aws_iam_role_policies_exclusive" "jupyterhub_cost_monitoring_iam_role_policies_exclusive" {
  count        = var.enable_jupyterhub_cost_monitoring ? 1 : 0
  role_name    = aws_iam_role.jupyterhub_cost_monitoring_iam_role[count.index].name
  policy_names = [aws_iam_role_policy.jupyterhub_cost_monitoring_iam_policy[count.index].name]
}

output "jupyterhub_cost_monitoring_k8s_sa_annotation" {
  value = var.enable_jupyterhub_cost_monitoring ? "eks.amazonaws.com/role-arn: ${aws_iam_role.jupyterhub_cost_monitoring_iam_role[0].arn}" : null
}

# 1. Allow opt-out of inconsistent legacy tags (define our internal tags)
# 2. Register our internal tags with AWS
# 3. Union the tags that we set on resources

locals {
  # Define tags that we register with AWS.
  # Do not set legacy tags if not needed.
  internal_cluster_name_tags   = toset(concat(var.enable_legacy_2i2c_tags ?["2i2c.org/cluster-name"]:[],["JHCM:ClusterName"] ) )
  internal_hub_name_tags       = toset(concat(var.enable_legacy_2i2c_tags ?["2i2c:hub-name"]:[],["JHCM:HubName"] ) )
  internal_node_purpose_tags   = toset(concat(var.enable_legacy_2i2c_tags ?["2i2c:node-purpose"]:[],["JHCM:Purpose"] ) )
  internal_volume_purpose_tags = toset(concat(var.enable_legacy_2i2c_tags ?["2i2c:volume-purpose"]:[],["JHCM:Purpose"] ) )

  # Define tags we'll register on resources
  # This _includes_ external tags that we do not wish to register with AWS (i.e. if the cost monitoring )
  cluster_name_tags            = var.external_cost_tags == null ? local.internal_cluster_name_tags: setunion(local.internal_cluster_name_tags, [var.external_cost_tags.cluster_name] )
  hub_name_tags                = var.external_cost_tags == null ? local.internal_hub_name_tags: setunion(local.internal_hub_name_tags, [var.external_cost_tags.hub_name] )
  # Semantically, these are identical, but historically were separate
  node_purpose_tags            = var.external_cost_tags == null ? local.internal_node_purpose_tags: setunion(local.internal_node_purpose_tags, [var.external_cost_tags.purpose] )
  volume_purpose_tags          = var.external_cost_tags == null ? local.internal_volume_purpose_tags: setunion(local.internal_volume_purpose_tags, [var.external_cost_tags.purpose] )
  intrinsic_cost_tags          = toset([
    "alpha.eksctl.io/cluster-name",
    "kubernetes.io/cluster/{var_cluster_name}",
    "kubernetes.io/created-for/pvc/name",
    "kubernetes.io/created-for/pvc/namespace",
  ] )
}
# If enable_jupyterhub_cost_tags = true, then activate cost allocation tags for the AWS Cost Explorer. Can take up to 24 hours to activate after being applied to a resource.
# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag
resource "aws_ce_cost_allocation_tag" "cost_allocation_tags" {
  for_each = var.enable_jupyterhub_cost_tags && var.external_cost_tags == null ? setunion(local.internal_cluster_name_tags, local.internal_hub_name_tags, local.internal_volume_purpose_tags, local.internal_node_purpose_tags, local.intrinsic_cost_tags) : toset([])

  tag_key = replace(each.key, "{var_cluster_name}", var.cluster_name)
  status  = "Active"
}
