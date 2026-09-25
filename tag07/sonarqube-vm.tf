terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Suche das neueste Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Lese SSH Public Key falls vorhanden
locals {
  ssh_public_key = try(file("${pathexpand("~")}/.ssh/id_rsa.pub"), null)
}

# AWS Key Pair für SSH Zugriff (falls SSH Public Key existiert)
resource "aws_key_pair" "sonarqube" {
  count           = local.ssh_public_key != null ? 1 : 0
  key_name        = "sonarqubekey"
  public_key      = trim(local.ssh_public_key, "\n")

  tags = {
    Name = "sonarqube-keypair"
  }
}

# Security Group für SonarQube VM
resource "aws_security_group" "sonarqube" {
  name        = "sonarqube-sg"
  description = "Security group for SonarQube VM"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SSH
  }

  ingress {
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SonarQube
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Cloud-Init mit SSH-Key Injizierung
locals {
  cloud_init_base = file("${path.module}/cloud-init.yml")
  cloud_init_with_ssh = local.ssh_public_key != null ? "${local.cloud_init_base}\nusers:\n  - name: ubuntu\n    sudo: ['ALL=(ALL) NOPASSWD:ALL']\n    ssh_authorized_keys:\n      - ${trim(local.ssh_public_key, "\n")}" : local.cloud_init_base
}

# EC2 Instance
resource "aws_instance" "sonarqube" {
  ami                    = data.aws_ami.ubuntu.id  # Neuestes Ubuntu 26.04 LTS
  instance_type          = "t3.large"              # Min 8GB RAM
  vpc_security_group_ids = [aws_security_group.sonarqube.id]
  key_name               = local.ssh_public_key != null ? aws_key_pair.sonarqube[0].key_name : null
  user_data              = base64encode(local.cloud_init_with_ssh)

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 30
    delete_on_termination = true
  }

  tags = {
    Name = "sonarqube-server"
  }
}

# Output für SSH Verbindung
output "ssh_command" {
  value       = local.ssh_public_key != null ? "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.sonarqube.public_ip}" : "SSH-Key nicht gefunden. Bitte ~/.ssh/id_rsa.pub erstellen."
  description = "SSH Befehl um sich mit der VM zu verbinden"
}

# Elastic IP
resource "aws_eip" "sonarqube" {
  instance = aws_instance.sonarqube.id
  domain   = "vpc"

  tags = {
    Name = "sonarqube-eip"
  }
}

# Output
output "sonarqube_ip" {
  value       = aws_eip.sonarqube.public_ip
  description = "Elastic IP für SonarQube"
}

output "sonarqube_url" {
  value       = "http://${aws_eip.sonarqube.public_ip}:9000"
  description = "SonarQube URL"
}
output "sonarqube_login" {
  value       = "Username=admin, Password=admin"
  description = "SonarQube URL"
}

output "startup_notice" {
  value       = "SonarQube needs about 5 minutes to start up..."
  description = "Startup time notice"
}
