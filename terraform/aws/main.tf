terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
  backend "gcs" {
    bucket = "two-eye-two-see-org-terraform-state"
    prefix = "terraform/state/pilot-hubs"
  }
}

provider "aws" {
  region = var.region
}

data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}
