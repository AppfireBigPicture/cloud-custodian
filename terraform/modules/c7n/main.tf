# IAM Role and policies for EC2 instance
resource "aws_iam_role" "this" {
  name = var.instance_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "CloudCustodianMailerAdmin" {
  name        = "CloudCustodianMailerAdmin"
  description = "Allow c7n to manage messages"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "sqs:DeleteMessage",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ],
        Resource = aws_sqs_queue.this.arn
      }
    ]
  })
}

resource "aws_iam_policy" "assume_appfire_policy" {
  name        = "CloudCustodianMultiAccount"
  description = "Allows assuming any role named AppfireCloudCustodian in any account of the organization"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : "sts:AssumeRole",
        "Resource" : "arn:aws:iam::*:role/AppfireCloudCustodian"
      }
    ]
  })
}

resource "aws_iam_policy" "ssm" {
  name        = "c7n-ssmquerypolicy"
  description = "Allow queries to SSM Parameter Store"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_query_attach" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.ssm.arn
}

resource "aws_iam_role_policy_attachment" "ssm_managed_instance_attach" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "c7n-assume-roles" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.CloudCustodianMailerAdmin.arn
}

resource "aws_iam_role_policy_attachment" "c7n-mailer-admin" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.assume_appfire_policy.arn
}

resource "aws_iam_instance_profile" "this" {
  name = "ec2-ssm-query-instance-profile"
  role = aws_iam_role.this.name
}

resource "aws_sqs_queue" "this" {
  name = "appfire-queue"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowAppfireCloudCustodianRoles",
        Effect    = "Allow",
        Principal = "*",
        Action = [
          "sqs:DeleteMessage",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ],
        Resource = aws_sqs_queue.this.arn,
        Condition = {
          ArnLike = {
            "aws:PrincipalArn" = "arn:aws:iam::*:role/${var.instance_role_name}*"
          }
        }
      }
    ]
  })
}

resource "aws_ssm_parameter" "this" {
  name           = var.sqs_parameter_name
  description    = "ARN of the SQS queue for Cloud Custodian"
  type           = "String"
  insecure_value = aws_sqs_queue.this.arn
}