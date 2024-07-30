# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ce_cost_allocation_tag
resource "aws_ce_cost_allocation_tag" "cost_allocation_tags" {
  for_each = toset(var.active_cost_allocation_tags)

  tag_key = replace(each.key, "{var_cluster_name}", var.cluster_name)
  status  = "Active"
}
