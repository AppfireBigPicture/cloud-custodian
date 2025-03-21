variable "aws_region" {
  description = <<-DESC
    AWS region where the resources will be deployed.

    Attributes:
      - Type: string
      - Default: "us-east-1"

    Example:
      "us-west-2"
  DESC
  type        = string
  default     = "us-east-1"
}

variable "common_tags" {
  description = <<-DESC
    A map of common tags applied to all resources for consistent tracking and cost allocation.

    Attributes:
      - Type: map(string)
      - Default:
        {
          Environment    = "Production"
          DeploymentType = "Automation"
          Brand          = "Appfire"
          AppCategory    = "DevOps"
          AdminEmail     = "bp-team-devops@appfire.com"
          OwningOrg      = "DevOps"
        }

    Example:
      {
        Environment    = "Staging"
        DeploymentType = "Manual"
        Brand          = "Appfire"
        AppCategory    = "DevOps"
        AdminEmail     = "team@appfire.com"
        OwningOrg      = "DevOps"
      }
  DESC
  type        = map(string)
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
  description = <<-DESC
    The EC2 instance type to launch.

    Attributes:
      - Type: string
      - Default: "t3.medium"

    Example:
      "t2.micro"
  DESC
  type        = string
  default     = "t3.medium"
}
