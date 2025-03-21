# Network
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "c7n-${var.environment}-vpc"
  }
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.subnet_cidr

  tags = {
    Name = "c7n-${var.environment}-subnet"
  }
}

resource "aws_security_group" "this" {
  vpc_id = aws_vpc.this.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c7n-${var.environment}-sg-ssm"
  }
}

resource "aws_vpc_endpoint" "ssm" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-${var.environment}-ssm-vpc-endpoint"
  }
}

resource "aws_vpc_endpoint" "ssm_messages" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ssmmessages"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-${var.environment}-ssm-messages-vpc-endpoint"
  }
}

resource "aws_vpc_endpoint" "ec2_messages" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ec2messages"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-${var.environment}-ec2-messages-vpc-endpoint"
  }
}

data "aws_ssm_parameter" "this" {
  name = "arn:aws:ssm:${var.aws_region}:533267137459:parameter/GoldenAMI/Ubuntu-24.04/latestID"
}

resource "aws_instance" "this" {
  ami                  = data.aws_ssm_parameter.this.value
  instance_type        = var.instance_type
  iam_instance_profile = var.instance_profile
  subnet_id            = aws_subnet.this.id

  tags = {
    Name         = "c7n-${var.environment}-docker-01"
    Exposure     = "Internal"
    EndpointType = "Workstation"
  }

  volume_tags = {
    DataClassification = "Confidential"
  }

  user_data = <<-EOF
              #!/bin/bash
              if ! command -v docker >/dev/null 2>&1; then
                echo "Docker not found. Installing..."
                curl -fsSL https://get.docker.com -o get-docker.sh && \
                sh get-docker.sh && \
                rm get-docker.sh
              fi
              docker pull softwareplant/c7n:0.1.0
              docker run --rm softwareplant/c7n:0.1.0
              shutdown -h now
              EOF
}

resource "aws_iam_role" "this" {
  name = "lambda-c7n-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Effect = "Allow",
      Sid    = ""
    }]
  })
}

resource "aws_iam_policy" "this" {
  name        = "c7n-${var.environment}-start-ec2"
  description = "Allow Lambda to start EC2 instances"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["ec2:StartInstances", "ec2:DescribeInstances"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.this.arn
}

resource "aws_lambda_function" "this" {
  function_name = "c7n-${var.environment}-start-ec2"
  role          = aws_iam_role.this.arn
  handler       = "index.handler"
  runtime       = "nodejs14.x"
  timeout       = 60

  filename = "../lambda.zip"

  environment {
    variables = {
      EC2_INSTANCE_ID = aws_instance.this.id
    }
  }

  tags = {
    Exposure = "Internal"
  }
}

resource "aws_cloudwatch_event_rule" "this" {
  name                = "every_24_hours_rule"
  description         = "Run Lambda every 24 hours"
  schedule_expression = "cron(0 21 * * ? *)"
}

resource "aws_cloudwatch_event_target" "this" {
  rule     = aws_cloudwatch_event_rule.this.name
  arn      = aws_lambda_function.this.arn
  role_arn = aws_iam_role.this.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "allow_execution_from_eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
