# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role
resource "aws_iam_role" "aws_ce_grafana_backend_iam_role" {
  count = var.enable_aws_ce_grafana_backend_iam ? 1 : 0

  name = "aws_ce_grafana_backend_iam_role"

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
          "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:support:aws-ce-grafana-backend"
        }
      },
    }]
  })
}

resource "aws_iam_role_policy" "aws_ce_grafana_backend_iam_policy" {
  count = var.enable_aws_ce_grafana_backend_iam ? 1 : 0
  name  = "aws_ce_grafana_backend_iam_policy"
  role  = aws_iam_role.aws_ce_grafana_backend_iam_role[count.index].name
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

resource "aws_iam_role_policies_exclusive" "aws_ce_grafana_backend_iam_role_policies_exclusive" {
  count        = var.enable_aws_ce_grafana_backend_iam ? 1 : 0
  role_name    = aws_iam_role.aws_ce_grafana_backend_iam_role[count.index].name
  policy_names = [aws_iam_role_policy.aws_ce_grafana_backend_iam_policy[count.index].name]
}

output "aws_ce_grafana_backend_k8s_sa_annotation" {
  value = var.enable_aws_ce_grafana_backend_iam ? "eks.amazonaws.com/role-arn: ${aws_iam_role.aws_ce_grafana_backend_iam_role[0].arn}" : null
}
