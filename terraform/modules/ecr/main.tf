resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}

output "repository_url" {
  value = aws_ecr_repository.main.repository_url
}

variable "project_name" {}
