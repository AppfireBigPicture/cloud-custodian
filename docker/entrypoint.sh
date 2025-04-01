#!/bin/bash

# Function to retrieve a parameter from AWS SSM
get_ssm_parameter() {
  local parameter_name=$1
  aws ssm get-parameter --name "$parameter_name" --with-decryption --query "Parameter.Value" --output text
}

# Function to prepare configuration files for Cloud Custodian
prepare_config_files() {
  envsubst < config/config.yaml.template > config/config.yaml
}

# Function to run the policy generator script
run_policy_generator() {
  python scripts/policy_generator.py
}

# Main function to execute the entrypoint logic
main() {
  QUEUE_ARN=$(get_ssm_parameter "/c7n/queue_arn")
  export QUEUE_ARN
  SLACK_WEBHOOK_URL=$(get_ssm_parameter "/c7n/slack_webhook_url")
  export SLACK_WEBHOOK_URL
  # AWS_REGION and ROLE_ARN are defined in the .env file as they are not sensitive information.


  prepare_config_files
  run_policy_generator

  exec "$@"
}

# Execute the main function
main "$@"