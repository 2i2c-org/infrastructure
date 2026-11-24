resource "aws_guardduty_detector" "guardduty" {
  enable = true
}

resource "aws_guardduty_detector_feature" "disabled_features" {
  for_each = toset(["S3_DATA_EVENTS", "RDS_LOGIN_EVENTS", "LAMBDA_NETWORK_LOGS", "EKS_RUNTIME_MONITORING"])
  detector_id = aws_guardduty_detector.guardduty.id
  name        = each.value
  status      = "DISABLED"
}

resource "aws_guardduty_detector_feature" "enabled_features" {
  for_each = toset(["EKS_AUDIT_LOGS"])
  detector_id = aws_guardduty_detector.guardduty.id
  name        = each.value
  status      = "ENABLED"
}

resource "aws_guardduty_detector_feature" "enable_agents" {
  detector_id = aws_guardduty_detector.guardduty.id
  name        = "RUNTIME_MONITORING"
  status      = "ENABLED"

  additional_configuration {
    name = "EKS_ADDON_MANAGEMENT"
    status = "ENABLED"
  }

  additional_configuration {
    name = "EC2_AGENT_MANAGEMENT"
    status = "ENABLED"
  }

  additional_configuration {
    # Explicitly set this here to prevent terraform from flip-flopping
    name = "ECS_FARGATE_AGENT_MANAGEMENT"
    status = "DISABLED"
  }
}


data "sops_file" "pagerduty_guardduty_integration" {
  # Read sops encrypted file containing integration key for pagerduty
  source_file = "secret/enc-pagerduty-guardduty-integration.yaml"
}

resource "aws_sns_topic" "guardduty" {
  name = "guardduty-findings-2i2c"
}

resource "aws_sns_topic_subscription" "guardduty_https_target" {
  topic_arn = aws_sns_topic.guardduty.arn
  protocol  = "https"
  endpoint  = data.sops_file.pagerduty_guardduty_integration.data["pagerdutyIntegration.url"]
}

resource "aws_cloudwatch_event_rule" "guardduty_finding" {
  name        = "guardduty-to-sns"

  event_pattern = jsonencode({
    source = ["aws.guardduty"]
    detail-type = [
      "GuardDuty Finding"
    ]
  })
}

resource "aws_cloudwatch_event_target" "guardduty" {
  rule      = aws_cloudwatch_event_rule.guardduty_finding.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.guardduty.arn
}


resource "aws_sns_topic_policy" "guardduty" {
  arn    = aws_sns_topic.guardduty.arn
  policy = data.aws_iam_policy_document.guardduty_topic_policy.json
}

data "aws_iam_policy_document" "guardduty_topic_policy" {
  statement {
    effect  = "Allow"
    actions = ["SNS:Publish"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [aws_sns_topic.guardduty.arn]
  }
}
