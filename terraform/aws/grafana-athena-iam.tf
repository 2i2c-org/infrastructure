resource "aws_iam_role" "grafana_athena_role" {
  count = var.enable_grafana_athena_iam ? 1 : 0

  name = "${var.cluster_name}-grafana-athena"
  tags = var.tags

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid = "AthenaQueryAccess"
      Effect = "Allow"
      Action = [
        "sts:AssumeRoleWithWebIdentity",
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
      Sid = "GlueReadAccess"
      Effect = "Allow"
      Action = [
        "sts:AssumeRoleWithWebIdentity",
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
      Sid = "AthenaS3Access"
      Effect = "Allow"
      Action = [
        "sts:AssumeRoleWithWebIdentity",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListMultipartUploadParts",
        "s3:AbortMultipartUpload",
        "s3:PutObject"
      ]
      Resource = ["arn:aws:s3:::aws-athena-query-results-*"]
    },
    {
      Sid = "AthenaExamplesS3Access"
      Effect = "Allow"
      Action = [
        "sts:AssumeRoleWithWebIdentity",
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = ["arn:aws:s3:::athena-examples*"]
    }]
  })
}

output "grafana_athena_iam_annotation" {
  value = "eks.amazonaws.com/role-arn: ${aws_iam_role.grafana_athena_role[0].arn}"
}
