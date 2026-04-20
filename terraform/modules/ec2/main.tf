# Generate SSH Key Pair for EC2 access
resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "generated_key" {
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.main.public_key_openssh
}

# Create a single Elastic IP for the server
resource "aws_eip" "server_ip" {
  instance = aws_instance.server.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-server-eip"
  }
}

# Fetch the latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_instance" "server" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"
  
  subnet_id                   = var.public_subnet_id
  vpc_security_group_ids      = [var.ec2_sg_id]
  key_name                    = aws_key_pair.generated_key.key_name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              # Update and Install Docker
              dnf update -y
              dnf install -y docker
              systemctl start docker
              systemctl enable docker
              usermod -a -G docker ec2-user

              # Install Docker Compose as a plugin
              DOCKER_CONFIG=/usr/local/lib/docker
              mkdir -p $DOCKER_CONFIG/cli-plugins
              curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
              chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

              # Note: For full automation, we would pull the git repo here.
              # For now, this sets up the environment.
              mkdir -p /home/ec2-user/app
              EOF

  tags = {
    Name = "${var.project_name}-server"
  }
}

variable "project_name" {}
variable "public_subnet_id" {}
variable "ec2_sg_id" {}

output "public_ip" {
  value = aws_eip.server_ip.public_ip
}

output "private_key" {
  value     = tls_private_key.main.private_key_pem
  sensitive = true
}
