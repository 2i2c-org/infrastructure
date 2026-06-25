// Cost monitoring resources for IAM role and cost allocation tags.
// Note: if the name of the IAM role is changed, then update the config in helm-charts/support/values.jsonnet for the k8s service account annotation.

resource "aws_iam_role" "jupyterhub_grafana_cloudwatch" {
  name = "jupyterhub_grafana_cloudwatch"

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
          "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:support:support-grafana"
        }
      },
    }]
  })
}

resource "aws_iam_role_policy" "jupyterhub_grafana_cloudwatch" {
  name = "jupyterhub_grafana_cloudwatch"
  role = aws_iam_role.jupyterhub_grafana_cloudwatch.name
  # ref: https://grafana.com/docs/grafana/latest/datasources/aws-cloudwatch/configure/#iam-policy-examples
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "AllowReadingMetricsFromCloudWatch",
        "Effect" : "Allow",
        "Action" : [
          "CloudWatch:DescribeAlarmsForMetric",
          "CloudWatch:DescribeAlarmHistory",
          "CloudWatch:DescribeAlarms",
          "CloudWatch:ListMetrics",
          "CloudWatch:GetMetricData",
          "CloudWatch:GetInsightRuleReport"
        ],
        "Resource" : "*"
      }
    ]
  })
}

resource "aws_iam_role_policies_exclusive" "jupyterhub_grafana_cloudwatch" {
  role_name    = aws_iam_role.jupyterhub_grafana_cloudwatch.name
  policy_names = [aws_iam_role_policy.jupyterhub_grafana_cloudwatch.name]
}

output "jupyterhub_grafana_cloudwatch_k8s_sa_annotation" {
  value = "eks.amazonaws.com/role-arn: ${aws_iam_role.jupyterhub_grafana_cloudwatch.arn}"
}