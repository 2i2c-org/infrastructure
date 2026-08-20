
resource "aws_eks_cluster" "cluster" {
  count = var.use_eksctl ? 0 : 1

  name = "${var.cluster_name}-cluster"

  access_config {
    authentication_mode = "API"
  }

  role_arn = aws_iam_role.cluster[0].arn
  version  = var.k8s_versions.min_master_version

  vpc_config {
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

  cidr_block           = "192.168.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = var.use_eksctl ? 0 : length(data.aws_availability_zones.available.names)
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = "192.168.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "public" {
  count                   = var.use_eksctl ? 0 : length(data.aws_availability_zones.available.names)
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = "192.168.${count.index + 10}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "${var.cluster_name}-public-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

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


  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = var.core_nodes.disk_size_gb
      volume_type = var.core_nodes.disk_type
      iops        = var.core_nodes.disk_iops
      throughput  = var.core_nodes.disk_throughput
    }
  }
}

resource "aws_eks_node_group" "core" {
  count           = var.use_eksctl ? 0 : 1
  cluster_name    = aws_eks_cluster.cluster[0].name
  node_group_name = "${var.cluster_name}-core-pool"
  node_role_arn   = aws_iam_role.cluster[0].arn
  subnet_ids      = aws_subnet.public[*].id
  ami_type        = "AL2023_x86_64_STANDARD"

  launch_template {
    id = aws_launch_template.core[0].id
    # TODO: check this is correct
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
  )
}

resource "aws_launch_template" "notebook" {
  for_each = var.use_eksctl ? {} : var.notebook_nodes
  name     = "${var.cluster_name}-notebook-${each.key}"

  instance_type = each.value.machine_type

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = each.value.disk_size_gb
      volume_type = each.value.disk_type
      iops        = each.value.disk_iops
      throughput  = each.value.disk_throughput
    }
  }

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
  subnet_ids      = aws_subnet.public[*].id
  ami_type        = "AL2023_x86_64_STANDARD"

  launch_template {
    # TODO fixme this seems long winded
    id = aws_launch_template.notebook[each.key].id
    # TODO: check this is correct
    version = aws_launch_template.notebook[each.key].default_version
  }

  node_repair_config {
    enabled = true
  }

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
  )
}
