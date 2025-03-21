resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/24"

  tags = {
    Name = "c7n-prod-vpc"
  }
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = "10.0.0.0/26"

  tags = {
    Name = "c7n-prod-subnet"
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
    Name = "c7n-prod-sg-ssm"
  }
}

resource "aws_vpc_endpoint" "ssm" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ssm"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-prod-ssm-vpc-endpoint"
  }
}

resource "aws_vpc_endpoint" "ssm_messages" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ssmmessages"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-prod-ssm-messages-vpc-endpoint"
  }
}

resource "aws_vpc_endpoint" "ec2_messages" {
  vpc_id             = aws_vpc.this.id
  service_name       = "com.amazonaws.${var.aws_region}.ec2messages"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.this.id]
  security_group_ids = [aws_security_group.this.id]

  tags = {
    Name = "c7n-prod-ec2-messages-vpc-endpoint"
  }
}

resource "aws_iam_role" "ssm" {
  name = "ec2-c7n-prod"

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

resource "aws_iam_policy" "ssm" {
  name        = "c7n-prod-ssmquerypolicy"
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
  role       = aws_iam_role.ssm.name
  policy_arn = aws_iam_policy.ssm.arn
}

resource "aws_iam_role_policy_attachment" "ssm_managed_instance_attach" {
  role       = aws_iam_role.ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "this" {
  name = "ec2-ssm-query-instance-profile"
  role = aws_iam_role.ssm.name
}

resource "aws_iam_role" "lambda" {
  name = "lambda-c7n-prod"

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

resource "aws_iam_policy" "ec2" {
  name        = "c7n-prod-start-ec2"
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

resource "aws_iam_role_policy_attachment" "lambda_ec2_attach" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.ec2.arn
}

data "aws_ssm_parameter" "this" {
  name = "arn:aws:ssm:${var.aws_region}:533267137459:parameter/GoldenAMI/Ubuntu-24.04/latestID"
}

resource "aws_instance" "this" {
  ami                  = data.aws_ssm_parameter.this.value
  instance_type        = var.instance_type
  iam_instance_profile = aws_iam_instance_profile.this.name
  subnet_id            = aws_subnet.this.id

  tags = {
    Name         = "c7n-prod-docker-01"
    Exposure     = "Internal"
    EndpointType = "Workstation"
  }
  volume_tags = {
    DataClassification = "Confidential"
  }

  user_data = <<-EOF
              #!/bin/bash

              # Install Docker if not present
              if ! command -v docker >/dev/null 2>&1; then
                echo "Docker not found. Installing..."
                curl -fsSL https://get.docker.com -o get-docker.sh && \
                sh get-docker.sh && \
                rm get-docker.sh
              fi

              # Pull the Docker image
              docker pull softwareplant/c7n:0.1.0

              # Run the container and remove it after execution
              docker run --rm softwareplant/c7n:0.1.0

              # Shutdown the instance once the container finishes
              shutdown -h now

              EOF
}

resource "aws_lambda_function" "this" {
  function_name = "c7n-prod-start-ec2"
  role          = aws_iam_role.lambda.arn
  handler       = "index.handler"
  runtime       = "nodejs14.x"
  timeout       = 60

  filename = "./lambda.zip"

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
  role_arn = aws_iam_role.lambda.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "allow_execution_from_eventbridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
