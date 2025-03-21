variable "aws_region" {
  type        = string
  description = <<EOT
    (Optional) AWS region where the resources will be deployed.

    Default: us-east-1
  EOT

  default = "us-east-1"
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

variable "common_tags" {
  type        = map(string)
  description = <<EOT
    (Optional) A map of common tags applied to all resources for consistent tracking and cost allocation.

    Default:
      {
        Environment    = "Staging"
        DeploymentType = "Manual"
        Brand          = "Appfire"
        AppCategory    = "DevOps"
        AdminEmail     = "team@appfire.com"
        OwningOrg      = "DevOps"
      }
  EOT

  default = {
    Environment    = "Production"
    DeploymentType = "Automation"
    Brand          = "Appfire"
    AppCategory    = "DevOps"
    AdminEmail     = "bp-team-devops@appfire.com"
    OwningOrg      = "DevOps"
  }
}

variable "instance_type" {
  type        = string
  description = <<EOT
    (Optional) The EC2 instance type to launch.

    Default: t3.medium
  EOT

  default = "t3.medium"
}
