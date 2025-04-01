#!/bin/bash

set -euo pipefail

# Function to run Cloud Custodian policies
run_custodian_policies() {
  local config_file="accounts.yml"
  local policy_file="policies/policy.yml"
  local output_dir="output"

  c7n-org run --config "$config_file" --use "$policy_file" --output-dir "$output_dir"
}

# Function to run Cloud Custodian mailer
run_custodian_mailer() {
  local mailer_config="mailer.yml"
  local templates_dir="mailer-templates"

  c7n-mailer --config "$mailer_config" --templates "$templates_dir" --run
}

# Main function to execute the pipeline
main() {
  run_custodian_policies
  run_custodian_mailer
}

# Execute the main function
main