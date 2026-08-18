// IAM role for the fluent-bit deployment in the support chart, which ships
// Kubernetes Events to CloudWatch Logs.

locals {
  k8s_event_exporter_log_group_name = "/2i2c/${var.cluster_name}/k8s-events"
}

resource "aws_iam_role" "k8s_event_exporter_cloudwatch" {
  count = var.enable_k8s_event_exporter ? 1 : 0

  name = "k8s_event_exporter_cloudwatch"

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
          "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:support:support-fluent-bit"
        }
      },
    }]
  })
}

resource "aws_iam_role_policy" "k8s_event_exporter_cloudwatch" {
  count = var.enable_k8s_event_exporter ? 1 : 0
  name  = "k8s_event_exporter_cloudwatch"
  role  = aws_iam_role.k8s_event_exporter_cloudwatch[count.index].name
  # These are the permissions fluent-bit's cloudwatch_logs output needs given
  # we let it create the group itself and set a retention policy on it.
  # ref: https://docs.fluentbit.io/manual/data-pipeline/outputs/cloudwatch
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:PutRetentionPolicy",
        ],
        Resource = [
          "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.k8s_event_exporter_log_group_name}",
          "arn:${data.aws_partition.current.partition}:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.k8s_event_exporter_log_group_name}:*",
        ],
      },
    ]
  })
}

resource "aws_iam_role_policies_exclusive" "k8s_event_exporter_cloudwatch" {
  count        = var.enable_k8s_event_exporter ? 1 : 0
  role_name    = aws_iam_role.k8s_event_exporter_cloudwatch[count.index].name
  policy_names = [aws_iam_role_policy.k8s_event_exporter_cloudwatch[count.index].name]
}

output "k8s_event_exporter_cloudwatch_k8s_sa_annotation" {
  value = var.enable_k8s_event_exporter ? "eks.amazonaws.com/role-arn: ${aws_iam_role.k8s_event_exporter_cloudwatch[0].arn}" : null
}
