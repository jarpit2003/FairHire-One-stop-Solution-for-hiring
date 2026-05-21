resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.environment}"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "main" {
  identifier        = "${var.project}-${var.environment}"
  engine            = "postgres"
  engine_version    = "16"
  instance_class    = "db.t3.medium"
  allocated_storage = 20
  db_name           = "fairhire"
  username          = var.db_username
  password          = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids
  skip_final_snapshot    = false
  deletion_protection    = true
  storage_encrypted      = true

  tags = {
    Environment = var.environment
  }
}

output "endpoint" { value = aws_db_instance.main.endpoint }
