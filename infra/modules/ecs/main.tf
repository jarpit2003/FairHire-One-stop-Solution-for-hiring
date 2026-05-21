resource "aws_ecs_cluster" "main" {
  name = "${var.project}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

output "cluster_arn" { value = aws_ecs_cluster.main.arn }
