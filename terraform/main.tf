module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
}

module "security_groups" {
  source       = "./modules/security_groups"
  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
}

module "ecr" {
  source       = "./modules/ecr"
  project_name = var.project_name
}

module "rds" {
  source          = "./modules/rds"
  project_name    = var.project_name
  private_subnets = module.vpc.private_subnets
  rds_sg_id       = module.security_groups.rds_sg_id
  db_name         = var.db_name
  db_username     = var.db_username
  db_password     = var.db_password
}

module "iam" {
  source       = "./modules/iam"
  project_name = var.project_name
}


module "ecs" {
  source             = "./modules/ecs"
  project_name       = var.project_name
  aws_region         = var.aws_region
  public_subnets     = module.vpc.public_subnets
  ecs_sg_id          = module.security_groups.ecs_sg_id
  execution_role_arn = module.iam.execution_role_arn
  task_role_arn      = module.iam.task_role_arn
  repository_url     = module.ecr.repository_url
  db_endpoint        = module.rds.db_endpoint
  db_username        = var.db_username
  db_password        = var.db_password
  db_name            = var.db_name
}



output "ecr_repository_url" {
  value = module.ecr.repository_url
}

