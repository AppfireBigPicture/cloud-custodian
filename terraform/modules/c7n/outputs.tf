output "instance_profile_name" {
  description = "Instance profile name"
  value       = aws_iam_instance_profile.this.name
}

output "cloudcustodian_role_arn" {
  description = "Cloud Custodian role ARN"
  value       = aws_iam_role.this.arn
}

output "sqs_queue_arn" {
  description = "SQS queue ARN"
  value       = aws_sqs_queue.this.arn
}

output "mailer_sqs_parameter_name" {
  description = "Valor del parámetro SSM para CloudCustodian Mailer"
  value       = aws_ssm_parameter.this.name
}
