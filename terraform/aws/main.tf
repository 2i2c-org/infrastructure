terraform {
  required_providers {
    aws = {
      # ref: https://registry.terraform.io/providers/hashicorp/aws/latest
      source  = "hashicorp/aws"
      version = "~> 4.52"
    }

    mysql = {
      # ref: https://registry.terraform.io/providers/petoju/mysql/latest
      source  = "petoju/mysql"
      version = "~> 3.0"
    }

  }
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

provider "random" {}

provider "aws" {
  region = var.region
}

data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}
