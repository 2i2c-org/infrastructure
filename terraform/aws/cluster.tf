resource "aws_eks_cluster" "cluster" {
  name   = "${var.cluster_name}-cluster"
  region = var.region

  access_config {
    authentication_mode = "API"
  }

  role_arn = aws_iam_role.cluster.arn
  version  = var.k8s_versions.min_master_version

  vpc_config {
    subnet_ids = concat(aws_subnet.private[*].id, aws_subnet.public[*].idu)
  }

  # Ensure that IAM Role permissions are created before and deleted
  # after EKS Cluster handling. Otherwise, EKS will not be able to
  # properly delete EKS managed EC2 infrastructure such as Security Groups.
  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
  ]
}

resource "aws_iam_role" "cluster" {
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
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster.name
}


# Declare the data source
data "aws_availability_zones" "available" {
  state  = "available"
  region = var.region
}


resource "aws_vpc" "main" {
  region               = var.region
  cidr_block           = "192.168.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_subnet" "private" {
  region            = var.region
  count             = count(aws_availability_zones.available.names)
  vpc_id            = aws_vpc.main.id
  cidr_block        = "192.168.${count.index + 1}.0/24"
  availability_zone = aws_availability_zones.available.names[count.index]

  tags = {
    Name                              = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "public" {
  region                  = var.region
  count                   = count(aws_availability_zones.available.names)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "192.168.${count.index + 10}.0/24"
  availability_zone       = aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                     = "${var.cluster_name}-public-${count.index + 1}"
    "kubernetes.io/role/elb" = "1"
  }
}

resource "aws_iam_role" "node" {
  name = "${var.cluster_name}-node"

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
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node.name
}

resource "aws_iam_role_policy_attachment" "node-AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node.name
}

resource "aws_iam_role_policy_attachment" "node-AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node.name
}

resource "aws_launch_template" "core" {
  name = "${var.cluster-name}-core-machine"

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
  cluster_name    = aws_eks_cluster.cluster.name
  region          = var.region
  node_group_name = "${var.cluster-name}-core-pool"
  node_role_arn   = aws_iam_role.cluster.arn
  subnet_ids      = aws_subnet.public[*].id
  ami_type        = "AL2023_x86_64_STANDARD"

  launch_template {
    id = aws_launch_template.core.id
    # TODO: check this is correct
    version = aws_launch_template.core.default_version
  }

  node_repair_config {
    enabled = true
  }
  instance_types = [var.core_node_machine_type]

  scaling_config {
    min_size     = 1
    max_size     = var.core_node_max_count
    desired_size = 1
  }

  update_config {
    max_unavailable = 1
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node-AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node-AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node-AmazonEC2ContainerRegistryReadOnly,
  ]

  labels = merge({
    "hub.jupyter.org/node-purpose" = "core",
    "k8s.dask.org/node-purpose"    = "core"
    }, each.value.labels
  )

  tags = merge({
    "ManagedBy" : "2i2c",
    "2i2c.org/cluster-name" : aws_eks_cluster.cluster.name,
    "2i2c:node-purpose" : "core",
    }, each.value.tags
  )
}

resource "aws_launch_template" "notebook" {
  name = "${var.cluster-name}-notebook-machine"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = var.notebook_nodes.disk_size_gb
      volume_type = var.notebook_nodes.disk_type
      iops        = var.notebook_nodes.disk_iops
      throughput  = var.notebook_nodes.disk_throughput
    }
  }
}

resource "aws_eks_node_group" "notebook" {
  cluster_name    = aws_eks_cluster.cluster.name
  region          = var.region
  node_group_name = "${var.cluster-name}-notebook-pool"
  node_role_arn   = aws_iam_role.cluster.arn
  subnet_ids      = aws_subnet.public[*].id
  ami_type        = "AL2023_x86_64_STANDARD"

  launch_template {
    id = aws_launch_template.notebook.id
    # TODO: check this is correct
    version = aws_launch_template.notebook.default_version
  }

  node_repair_config {
    enabled = true
  }
  instance_types = [var.notebook_node_machine_type]

  scaling_config {
    min_size     = 1
    max_size     = var.notebook_node_max_count
    desired_size = 1
  }

  update_config {
    max_unavailable = 1
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node-AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node-AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node-AmazonEC2ContainerRegistryReadOnly,
  ]

  labels = merge({
    "hub.jupyter.org/node-purpose" = "user",
    "k8s.dask.org/node-purpose"    = "scheduler"
    }, each.value.labels
  )

  tags = merge({
    "ManagedBy" : "2i2c",
    "2i2c.org/cluster-name" : aws_eks_cluster.cluster.name,
    "2i2c:node-purpose" : "user",
    }, each.value.tags
  )
}
