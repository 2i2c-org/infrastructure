# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
resource "aws_iam_role" "jupyterhub_cost_monitoring_iam_role" {
  count = var.enable_jupyterhub_cost_monitoring_iam ? 1 : 0

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
  count = var.enable_jupyterhub_cost_monitoring_iam ? 1 : 0
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
  count        = var.enable_jupyterhub_cost_monitoring_iam ? 1 : 0
  role_name    = aws_iam_role.jupyterhub_cost_monitoring_iam_role[count.index].name
  policy_names = [aws_iam_role_policy.jupyterhub_cost_monitoring_iam_policy[count.index].name]
}

output "jupyterhub_cost_monitoring_k8s_sa_annotation" {
  value = var.enable_jupyterhub_cost_monitoring_iam ? "eks.amazonaws.com/role-arn: ${aws_iam_role.jupyterhub_cost_monitoring_iam_role[0].arn}" : null
}
