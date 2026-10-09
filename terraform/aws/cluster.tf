// Find out which subnets and security group our EFS / S3Files mount targets should be in
// It needs to be in the public subnet where our nodes are, as the nodes will be
// doing the mounting operation. It should be in a security group shared by all
// the nodes. We create a mount target for each EFS / S3Files, in each subnet, even if we
// primarily put all our nodes in one - this allows for GPU nodes to be spread
// out across AZ when needed
data "aws_subnets" "cluster_node_subnets" {

  filter {
    name   = "vpc-id"
    values = [data.aws_eks_cluster.cluster.vpc_config[0]["vpc_id"]]
  }

  filter {
    name   = "tag:aws:cloudformation:logical-id"
    values = ["SubnetPublic*"]
  }

  filter {
    name   = "tag:alpha.eksctl.io/cluster-name"
    values = [var.cluster_name]
  }
}

data "aws_security_group" "cluster_nodes_shared_security_group" {

  filter {
    name   = "vpc-id"
    values = [data.aws_eks_cluster.cluster.vpc_config[0]["vpc_id"]]
  }
  filter {
    name   = "tag:aws:cloudformation:logical-id"
    values = ["ClusterSharedNodeSecurityGroup"]
  }

  filter {
    name   = "tag:alpha.eksctl.io/cluster-name"
    values = [var.cluster_name]
  }
}