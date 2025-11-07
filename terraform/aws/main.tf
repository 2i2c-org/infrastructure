terraform {
  required_version = "~> 1.5"

  required_providers {
    aws = {
      # https://registry.terraform.io/providers/hashicorp/aws/latest
      source  = "hashicorp/aws"
      version = "~> 5.89"
    }

    mysql = {
      # https://registry.terraform.io/providers/petoju/mysql/latest
      source  = "petoju/mysql"
      version = "~> 3.0"
    }

    random = {
      # https://registry.terraform.io/providers/hashicorp/random/latest
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  backend "s3" {
    bucket = "grss-veda-tf-state-hub"
    key = "hub/terraform.tfstate"
    region = "us-west-2"
    dynamodb_table = "terraform-locks"
  }
}

# https://registry.terraform.io/providers/hashicorp/random/latest/docs
provider "random" {}

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
