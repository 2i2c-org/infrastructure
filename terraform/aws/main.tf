terraform {
  required_version = "~> 1.5"

  required_providers {
    aws = {
      # ref: https://registry.terraform.io/providers/hashicorp/aws/latest
      source  = "hashicorp/aws"
      version = "~> 5.57"
    }

    mysql = {
      # ref: https://registry.terraform.io/providers/petoju/mysql/latest
      source  = "petoju/mysql"
      version = "~> 3.0"
    }

    random = {
      # ref: https://registry.terraform.io/providers/hashicorp/random/latest
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

# ref: https://registry.terraform.io/providers/hashicorp/random/latest/docs
provider "random" {}

# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
provider "aws" {
  region = var.region

  # default_tags ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags-configuration-block
  default_tags {
    tags = {
      for k, v in var.default_tags : k => replace(v, "{var_cluster_name}", var.cluster_name)
    }
  }
}

# ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/eks_cluster
data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}
