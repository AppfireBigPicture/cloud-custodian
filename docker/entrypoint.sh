#!/bin/bash

QUEUE_ARN=$(aws ssm get-parameter --name "/c7n/queue_arn" --with-decryption --query "Parameter.Value" --output text)
export QUEUE_ARN
SLACK_WEBHOOK_URL=$(aws ssm get-parameter --name "/c7n/slack_webhook_url" --with-decryption --query "Parameter.Value" --output text)
export SLACK_WEBHOOK_URL
# AWS_REGION and ROLE_ARN are defined in the .env file as they are not sensitive information.

# Prepare config files for c7n
envsubst < config/config.yaml.template > config/config.yaml

python scripts/policy_generator.py

exec "$@"
