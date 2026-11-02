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


# FIXME: add OIDC for irsa etc.

resource "aws_eks_cluster" "cluster" {
  count = var.use_eksctl ? 0 : 1

  name = "${var.cluster_name}-cluster"

  access_config {
    authentication_mode = "API"
  }

  role_arn = aws_iam_role.cluster[0].arn
  version  = var.k8s_versions.min_master_version

  vpc_config {
    # endpoint_private/public
    # Security group IDs
    subnet_ids = concat(aws_subnet.private[*].id, aws_subnet.public[*].id)
  }

  # Ensure that IAM Role permissions are created before and deleted
  # after EKS Cluster handling. Otherwise, EKS will not be able to
  # properly delete EKS managed EC2 infrastructure such as Security Groups.
  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
  ]
}


resource "aws_iam_role" "cluster" {
  count = var.use_eksctl ? 0 : 1

  name = "${var.cluster_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  count = var.use_eksctl ? 0 : 1


  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster[0].name
}


# Declare the data source
data "aws_availability_zones" "available" {
  state = "available"
}


resource "aws_vpc" "main" {
  count = var.use_eksctl ? 0 : 1

  # TODO: set CIDR block from variable
  cidr_block           = "192.168.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_subnet" "private" {
  count  = var.use_eksctl ? 0 : length(data.aws_availability_zones.available.names)
  vpc_id = aws_vpc.main[0].id
  # FIXME: use cidrsubnet() to split the vpc CIDR block (variable) into a block according to a number of subnet bits (var, e.g. 3), and the count index
  cidr_block        = "192.168.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "public" {
  count  = var.use_eksctl ? 0 : length(data.aws_availability_zones.available.names)
  vpc_id = aws_vpc.main[0].id
  # FIXME: also use cidrsubnet as above, shift count by length of private subnet
  cidr_block              = "192.168.${count.index + 10}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "${var.cluster_name}-public-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

# FIXME: add aws_internet_gateway to allow VPC access to internet
#        https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html

# FIXME: add aws_route, aws_route_table, aws_route_table_association, aws_nat_gateway, and aws_eips for the nag gateway

resource "aws_iam_role" "node" {
  count = var.use_eksctl ? 0 : 1
  name  = "${var.cluster_name}-node"

  assume_role_policy = jsonencode({
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
    Version = "2012-10-17"
  })
}

# TODO: one role per node group?
resource "aws_iam_role_policy_attachment" "node-AmazonEKSWorkerNodePolicy" {
  count      = var.use_eksctl ? 0 : 1
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node[0].name
}

resource "aws_iam_role_policy_attachment" "node-AmazonEKS_CNI_Policy" {
  count      = var.use_eksctl ? 0 : 1
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node[0].name
}

resource "aws_iam_role_policy_attachment" "node-AmazonEC2ContainerRegistryReadOnly" {
  count      = var.use_eksctl ? 0 : 1
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node[0].name
}

resource "aws_launch_template" "core" {
  count = var.use_eksctl ? 0 : 1
  name  = "${var.cluster_name}-core-machine"

  instance_type = var.core_nodes.machine_type

  # FIXME: update_default_version?


  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = var.core_nodes.disk_size_gb
      volume_type = var.core_nodes.disk_type
      iops        = var.core_nodes.disk_iops
      throughput  = var.core_nodes.disk_throughput
    }
  }

  # FIXME: node placement, primary zone
  # FIXME: user_data to set maxPods?
}

resource "aws_eks_node_group" "core" {
  count           = var.use_eksctl ? 0 : 1
  cluster_name    = aws_eks_cluster.cluster[0].name
  node_group_name = "${var.cluster_name}-core-pool"
  node_role_arn   = aws_iam_role.cluster[0].arn
  # FIXME: only primary AZ (filter)
  subnet_ids = aws_subnet.public[*].id
  ami_type   = "AL2023_x86_64_STANDARD"

  launch_template {
    id      = aws_launch_template.core[0].id
    version = aws_launch_template.core[0].default_version
  }

  node_repair_config {
    enabled = true
  }

  scaling_config {
    min_size     = var.core_nodes.min
    max_size     = var.core_nodes.max
    desired_size = var.core_nodes.min
  }

  update_config {
    max_unavailable = 1
  }
  # FIXME: lifeccyle ignore changes to desired_size

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node-AmazonEKSWorkerNodePolicy[0],
    aws_iam_role_policy_attachment.node-AmazonEKS_CNI_Policy[0],
    aws_iam_role_policy_attachment.node-AmazonEC2ContainerRegistryReadOnly[0],
  ]

  dynamic "taint" {
    for_each = var.core_nodes.taints
    content {
      key    = each.key
      effect = each.value.effect
      value  = each.value.value
    }
  }

  /**
  Generate EC2 resource tags representing node taints that cluster autoscaler's autodiscovery understands
  https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup
  */
  # FIXME: store all labels under new var, pre merged
  labels = merge({
    "node.kubernetes.io/instance-type" = "${var.core_nodes.machine_type}",
    "hub.jupyter.org/node-purpose"     = "core",
    "k8s.dask.org/node-purpose"        = "core"
    }, var.core_nodes.labels
  )

  # https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup
  tags = merge({
    "ManagedBy" : "2i2c",
    "2i2c.org/cluster_name" : aws_eks_cluster.cluster[0].name,
    "2i2c:node-purpose" : "core",
    },
    var.core_nodes.tags,
    {
      for k, v in var.core_nodes.labels :
      "k8s.io/cluster-autoscaler/node-template/label/${k}" => v
    },
    {
      for k, v in var.core_nodes.taints :
      "k8s.io/cluster-autoscaler/node-template/taint/${k}" => "${v.value}:${v.effect}"
    }
    # FIXME: add cluster-autoscaler/enabled and ${var.cluster_name} = owned
    #        if the cluster autoscaler config requires it
  )
}

resource "aws_launch_template" "notebook" {
  for_each = var.use_eksctl ? {} : var.notebook_nodes
  name     = "${var.cluster_name}-notebook-${each.key}"

  instance_type = each.value.machine_type
  # FIXME: update_default_version

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = each.value.disk_size_gb
      volume_type = each.value.disk_type
      iops        = each.value.disk_iops
      throughput  = each.value.disk_throughput
    }
  }

  # FIXME: set placement into primary availability_zone
  # FIXME: set nodeconfig maxPods

  user_data = base64encode(<<-EOT
---
apiVersion: node.eks.aws/v1alpha1
kind: NodeConfig
spec:
  kubelet:
    config:
      singleProcessOOMKill: true
  EOT
  )
}

resource "aws_eks_node_group" "notebook" {
  for_each = var.use_eksctl ? {} : var.notebook_nodes

  cluster_name    = aws_eks_cluster.cluster[0].name
  node_group_name = "${var.cluster_name}-notebook-pool"
  node_role_arn   = aws_iam_role.cluster[0].arn
  # FIXME: primary AZ
  subnet_ids = aws_subnet.public[*].id
  ami_type   = "AL2023_x86_64_STANDARD"

  launch_template {
    # TODO fixme this seems long winded
    id = aws_launch_template.notebook[each.key].id
    # TODO: check this is correct
    version = aws_launch_template.notebook[each.key].default_version
  }

  node_repair_config {
    enabled = true
  }

  # FIXME: lifecycle ignore changes to desired size

  scaling_config {
    min_size     = each.value.min
    max_size     = each.value.max
    desired_size = each.value.min
  }

  update_config {
    max_unavailable = 1
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node-AmazonEKSWorkerNodePolicy[0],
    aws_iam_role_policy_attachment.node-AmazonEKS_CNI_Policy[0],
    aws_iam_role_policy_attachment.node-AmazonEC2ContainerRegistryReadOnly[0],
  ]

  dynamic "taint" {
    for_each = each.value.taints
    content {
      key    = each.key
      effect = each.value.effect
      value  = each.value.value
    }
  }

  labels = merge({
    "node.kubernetes.io/instance-type" = "${each.value.machine_type}",
    "hub.jupyter.org/node-purpose"     = "user",
    "k8s.dask.org/node-purpose"        = "scheduler"
    }, each.value.labels
  )

  tags = merge({
    "ManagedBy" : "2i2c",
    "2i2c.org/cluster_name" : aws_eks_cluster.cluster[0].name,
    "2i2c:node-purpose" : "user",
    },
    each.value.tags,
    {
      for k, v in each.value.labels :
      "k8s.io/cluster-autoscaler/node-template/label/${k}" => v
    },
    {
      for k, v in each.value.taints :
      "k8s.io/cluster-autoscaler/node-template/taint/${k}" => "${v.value}:${v.effect}"
    }

    # FIXME: see above for the autoscaler
  )
}
