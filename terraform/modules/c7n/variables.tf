variable "instance_role_name" {
  type        = string
  description = <<EOT
    (Optional)  The name of the role attached to the EC2 instance.

    Default: AppfireCloudCustodian
  EOT

  default = "AppfireCloudCustodian"
}

variable "sqs_parameter_name" {
  type        = string
  description = <<EOT
    (Optional) The name of the SSM Parameter that will contain SQS queue ARN.
    This SHOULD NOT be changed. It is hardcoded in the docker image.

    Default: /c7n/queue_arn
  EOT

  default = "/c7n/queue_arn"
}
