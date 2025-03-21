output "vpc" {
  description = "Created VPC resource"
  value       = aws_vpc.this
}

output "subnet" {
  description = "Created main Subnet resource"
  value       = aws_subnet.this
}

output "security_group" {
  description = "Created SSM Security Group resource"
  value       = aws_security_group.this
}

output "instance" {
  description = "Created EC2 instance resource"
  value       = aws_instance.this
}

output "lambda_function" {
  description = "Created Lambda function resource"
  value       = aws_lambda_function.this
}

output "cloudwatch_event_rule" {
  description = "Created CloudWatch Events rule resource"
  value       = aws_cloudwatch_event_rule.this
}
