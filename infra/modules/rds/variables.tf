variable "project"            { type = string }
variable "environment"        { type = string }
variable "subnet_ids"         { type = list(string) }
variable "security_group_ids" { type = list(string) }
variable "db_username"        { type = string }
variable "db_password"        { type = string; sensitive = true }
