resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = var.private_subnets

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  allocated_storage      = 20
  db_name                = var.db_name
  engine                 = "postgres"
  engine_version         = "16.6"
  instance_class         = "db.t3.micro"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]
  skip_final_snapshot    = true # Set to false for production
  publicly_accessible    = false

  tags = {
    Name = "${var.project_name}-rds"
  }
}

output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

variable "project_name" {}
variable "private_subnets" { type = list(string) }
variable "rds_sg_id" {}
variable "db_name" {}
variable "db_username" {}
variable "db_password" {}
