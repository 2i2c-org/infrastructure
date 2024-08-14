resource "aws_iam_role" "grafana_athena_role" {
  count = var.enable_grafana_athena_iam ? 1 : 0

  name = "${var.cluster_name}-grafana-athena-iam-role"
  tags = var.tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{

      Effect = "Allow"
      Principal = {
        Federated = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}"
      },
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:support:support-grafana"
        }
      }
    }]
  })

  inline_policy {
    name = "${var.cluster_name}-grafana-athena-iam-policy"

    # Terraform's "jsonencode" function converts a
    # Terraform expression result to valid JSON syntax.
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Sid    = "AthenaQueryAccess"
        Effect = "Allow"
        Action = [
          "athena:ListDatabases",
          "athena:ListDataCatalogs",
          "athena:ListWorkGroups",
          "athena:GetDatabase",
          "athena:GetDataCatalog",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:GetTableMetadata",
          "athena:GetWorkGroup",
          "athena:ListTableMetadata",
          "athena:StartQueryExecution",
          "athena:StopQueryExecution"
        ]
        Resource = ["*"]
        },
        {
          Sid    = "GlueReadAccess"
          Effect = "Allow"
          Action = [
            "glue:GetDatabase",
            "glue:GetDatabases",
            "glue:GetTable",
            "glue:GetTables",
            "glue:GetPartition",
            "glue:GetPartitions",
            "glue:BatchGetPartition"
          ]
          Resource = ["*"]
        },
        {
          Sid    = "AthenaS3Access"
          Effect = "Allow"
          Action = [
            "s3:GetBucketLocation",
            "s3:GetObject",
            "s3:ListBucket",
            "s3:ListBucketMultipartUploads",
            "s3:ListMultipartUploadParts",
            "s3:AbortMultipartUpload",
            "s3:PutObject"
          ]
          Resource = ["arn:aws:s3:::${var.athena_storage_bucket}*"]
      }]
    })
  }
}

output "grafana_athena_iam_annotation" {
  value = var.enable_grafana_athena_iam ? "eks.amazonaws.com/role-arn: ${aws_iam_role.grafana_athena_role[0].arn}" : null
}
