variable "aws_region" {
  type        = string
  description = <<EOT
    (Optional) AWS region where the resources will be deployed.

    Default: us-east-1
  EOT
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = <<EOT
    (Optional)  The name of the environment where the resources will be deployed.

    Options:
      - dev
      - prod

    Default: prod
  EOT

  default = "prod"

  validation {
    condition     = can(regex("dev|prod", var.environment))
    error_message = "Err: environment name is not valid."
  }
}

variable "instance_type" {
  type        = string
  description = <<EOT
    (Optional) The EC2 instance type to launch.

    Default: t3.medium
  EOT
  default     = "t3.medium"
}

variable "vpc_cidr" {
  type        = string
  description = <<EOT
    (Optional) CICR of the VPC.

    Default: 10.0.0.0/24
  EOT

  default = "10.0.0.0/24"
}

variable "subnet_cidr" {
  type        = string
  description = <<EOT
    (Optional) CICDR of the subnet.

    Default: 10.0.0.0/26
  EOT

  default = "10.0.0.0/26"
}

variable "instance_profile" {
  type        = string
  description = <<EOT
    (Required) Name of the instance profile to attach to the EC2 instance.
  EOT
}