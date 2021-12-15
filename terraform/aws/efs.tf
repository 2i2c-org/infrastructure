// Find out which subnet and security group our EFS mount target should be in
// It needs to be in the public subnet where our nodes are, as the nodes will be
// doing the mounting operation. It should be in a security group shared by all
// the nodes.
data "aws_subnet" "cluster_node_subnet" {

  filter {
    name   = "vpc-id"
    values = [data.aws_eks_cluster.cluster.vpc_config[0]["vpc_id"]]
  }
  filter {
    name   = "availability-zone"
    values = [var.cluster_nodes_location]
  }

  filter {
    name   = "tag:aws:cloudformation:logical-id"
    values = ["SubnetPublic*"]
  }

  filter {
    name   = "tag:eksctl.cluster.k8s.io/v1alpha1/cluster-name"
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
    name   = "tag:eksctl.cluster.k8s.io/v1alpha1/cluster-name"
    values = [var.cluster_name]
  }
}

resource "aws_efs_file_system" "homedirs" {
  tags = {
    Name = "hub-homedirs"
  }
}

resource "aws_efs_mount_target" "homedirs" {
  file_system_id  = aws_efs_file_system.homedirs.id
  subnet_id       = data.aws_subnet.cluster_node_subnet.id
  security_groups = [data.aws_security_group.cluster_nodes_shared_security_group.id]
}

output "nfs_server_dns" {
  value = aws_efs_file_system.homedirs.dns_name
}
