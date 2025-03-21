output "instance_id" {
  description = "ID de la instancia EC2 desplegada"
  value       = aws_instance.this.id
}

output "lambda_function_arn" {
  description = "ARN de la función Lambda"
  value       = aws_lambda_function.this.arn
}
