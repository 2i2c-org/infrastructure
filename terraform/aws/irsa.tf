data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

resource "aws_iam_role" "irsa_role" {
  for_each = var.hub_cloud_permissions
  name     = "${var.cluster_name}-${each.key}"

  assume_role_policy = data.aws_iam_policy_document.irsa_role_assume[each.key].json
}

data "aws_iam_policy_document" "irsa_role_assume" {
  for_each = var.hub_cloud_permissions
  statement {

    effect = "Allow"

    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type = "Federated"

      identifiers = [
        "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values = [
        "system:serviceaccount:${each.key}:user-sa"
      ]
    }
  }
}

resource "aws_iam_policy" "extra_user_policy" {
  for_each    = { for hub_name, value in var.hub_cloud_permissions : hub_name => value if value.extra_iam_policy != "" }
  name        = "${var.cluster_name}-${each.key}-extra-user-policy"
  description = "Extra permissions granted to users on hub ${each.key} on ${var.cluster_name}"
  policy      = each.value.extra_iam_policy
}

resource "aws_iam_role_policy_attachment" "extra_user_policy" {
  for_each   = { for hub_name, value in var.hub_cloud_permissions : hub_name => value if value.extra_iam_policy != "" }
  role       = aws_iam_role.irsa_role[each.key].name
  policy_arn = aws_iam_policy.extra_user_policy[each.key].arn
}

output "kubernetes_sa_annotations" {
  value = {
    for k, v in var.hub_cloud_permissions :
    k => "eks.amazonaws.com/role-arn: ${aws_iam_role.irsa_role[k].arn}"
  }
  description = <<-EOT
  Annotations to apply to userServiceAccount in each hub to enable cloud permissions for them.

  Helm, not terraform, control namespace creation for us. This makes it quite difficult
  to create the appropriate kubernetes service account attached to the Google Cloud Service
  Account in the appropriate namespace. Instead, this output provides the list of annotations
  to be applied to the kubernetes service account used by jupyter and dask pods in a given hub.
  This should be specified under userServiceAccount.annotations (or basehub.userServiceAccount.annotations
  in case of daskhub) on a values file created specifically for that hub.
  EOT
}
