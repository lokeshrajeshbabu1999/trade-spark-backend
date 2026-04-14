terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Note: A real 'Big Company' setup would use an S3 backend here.
  # backend "s3" {
  #   bucket         = "trade-spark-terraform-state"
  #   key            = "backend/terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "terraform-lock"
  # }
}

provider "aws" {
  region = var.aws_region
}
