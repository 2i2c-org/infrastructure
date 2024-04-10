/*
  This file provides resources _per hub and role_. Each role is tied to a
  specific k8s ServiceAccount allowed to assume the role.

  - Role                 - for use by k8s ServiceAccount (user-sa, admin-sa)
  - Policy               - if extra_iam_policy is declared
  - RolePolicyAttachment - if extra_iam_policy is declared
*/

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}



locals {
  hub_role = flatten([
    for hub, hub_value in var.hub_cloud_permissions : [
      for role, role_value in hub_value : {
        // id is conservatively adjusted to not change any previous resource
        // name set to the hub's name when only "user-sa" roles were around
        id   = role == "user-sa" ? hub : "${hub}-${role}"
        hub  = hub
        role = role
        data = role_value
      }
    ]
  ])
}



data "aws_iam_policy_document" "irsa_role_assume" {
  for_each = { for index, hr in local.hub_role : hr.id => hr }
  statement {
    effect  = "Allow"
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
        "system:serviceaccount:${each.value.hub}:${each.value.role}"
      ]
    }
  }
}

resource "aws_iam_role" "irsa_role" {
  for_each = { for index, hr in local.hub_role : hr.id => hr }
  name     = "${var.cluster_name}-${each.key}"

  assume_role_policy = data.aws_iam_policy_document.irsa_role_assume[each.key].json
}



resource "aws_iam_policy" "extra_user_policy" {
  for_each = { for index, hr in local.hub_role : hr.id => hr if hr.data.extra_iam_policy != "" }
  name     = "${var.cluster_name}-${each.key}-extra-user-policy"

  description = "Extra permissions granted to users on hub ${each.key} on ${var.cluster_name}"
  policy      = each.value.data.extra_iam_policy
}

resource "aws_iam_role_policy_attachment" "extra_user_policy" {
  for_each   = { for index, hr in local.hub_role : hr.id => hr if hr.data.extra_iam_policy != "" }
  role       = aws_iam_role.irsa_role[each.key].name
  policy_arn = aws_iam_policy.extra_user_policy[each.key].arn
}



output "kubernetes_sa_annotations" {
  value = {
    for index, hr in local.hub_role :
    hr.id => "eks.amazonaws.com/role-arn: ${aws_iam_role.irsa_role[hr.id].arn}"
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
