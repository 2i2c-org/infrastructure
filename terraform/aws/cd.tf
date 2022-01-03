// Resources required for continuously deploying hubs to this cluster
resource "aws_iam_user" "continuous_deployer" {
  name = "hub-continuous-deployer"
}

resource "aws_iam_access_key" "continuous_deployer" {
  user = aws_iam_user.continuous_deployer.name
}

resource "aws_iam_user_policy" "continuous_deployer" {
  name = "eks-readonly"
  user = aws_iam_user.continuous_deployer.name

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
			"Effect": "Allow",
			"Action": "eks:DescribeCluster",
			"Resource": "*"
    }
  ]
}
EOF
}


locals {
  cd_creds = {
    "AccessKey" = {
      "UserName" : aws_iam_user.continuous_deployer.name,
      "AccessKeyId" : aws_iam_access_key.continuous_deployer.id,
      "SecretAccessKey" : aws_iam_access_key.continuous_deployer.secret
    }
  }
}

output "continuous_deployer_creds" {
  value     = jsonencode(local.cd_creds)
  sensitive = true
}
