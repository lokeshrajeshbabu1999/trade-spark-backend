data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

module "security_groups" {
  source       = "./modules/security_groups"
  project_name = var.project_name
  vpc_id       = data.aws_vpc.default.id
}

module "ec2" {
  source           = "./modules/ec2"
  project_name     = var.project_name
  public_subnet_id = data.aws_subnets.default.ids[0]
  ec2_sg_id        = module.security_groups.ec2_sg_id
}

output "server_public_ip" {
  value = module.ec2.public_ip
}

output "ssh_private_key" {
  value     = module.ec2.private_key
  sensitive = true
}
