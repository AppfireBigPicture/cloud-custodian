#!/usr/bin/env bash

# A best practices Bash script template with many useful functions. This file
# sources in the bulk of the functions from the source.sh file which it expects
# to be in the same directory. Only those functions which are likely to need
# modification are present in this file. This is a great combination if you're
# writing several scripts! By pulling in the common functions you'll minimise
# code duplication, as well as ease any potential updates to shared functions.

# Enable xtrace if the DEBUG environment variable is set
if [[ ${DEBUG-} =~ ^1|yes|true$ ]]; then
    set -o xtrace       # Trace the execution of the script (debug)
fi

# Only enable these shell behaviours if we're not being sourced
# Approach via: https://stackoverflow.com/a/28776166/8787985
if ! (return 0 2> /dev/null); then
    # A better class of script...
    set -o errexit      # Exit on most errors (see the manual)
    set -o nounset      # Disallow expansion of unset variables
    set -o pipefail     # Use last non-zero exit code in a pipeline
fi

# Enable errtrace or the error trap handler will not work as expected
set -o errtrace         # Ensure the error trap handler is inherited

# DESC: Usage help
# ARGS: None
# OUTS: None
# RETS: None
function script_usage() {
    cat << EOF
Usage:
     -h|--help                  Displays this help
     -v|--verbose               Displays verbose output
    -nc|--no-colour             Disables colour output
    -cr|--cron                  Run silently unless we encounter an error
EOF
}

# DESC: Parameter parser
# ARGS: $@ (optional): Arguments provided to the script
# OUTS: Variables indicating command-line parameters and options
# RETS: None
function parse_params() {
    local param
    while [[ $# -gt 0 ]]; do
        param="$1"
        shift
        case $param in
            -h | --help)
                script_usage
                exit 0
                ;;
            -v | --verbose)
                verbose=true
                ;;
            -nc | --no-colour)
                no_colour=true
                ;;
            -cr | --cron)
                cron=true
                ;;
            *)
                script_exit "Invalid parameter was provided: $param" 1
                ;;
        esac
    done
}

# Function to run Cloud Custodian policies
function run_custodian_policies() {
  local config_file="accounts.yml"
  local policy_file="policies/policy.yml"
  local output_dir="output"

  verbose_print "==> Running Cloud Custodian..." "$fg_cyan"
  c7n-org run \
    --config "$config_file" \
    --use "$policy_file" \
    --output-dir "$output_dir" || \
    script_exit "Failed to run Cloud Custodian policies" 1
  verbose_print "==> Cloud Custodian analisis completed successfully." "$fg_green"
}

# Function to run Cloud Custodian mailer
function run_custodian_mailer() {
  local mailer_config="mailer.yml"
  local templates_dir="mailer-templates"

  verbose_print "==> Running Cloud Custodian mailer..." "$fg_cyan"
  c7n-mailer \
    --config "$mailer_config" \
    --templates "$templates_dir" \
    --run ||\
    script_exit "Failed to run Cloud Custodian mailer" 1
  verbose_print "==> Cloud Custodian mailer completed successfully." "$fg_green"
}

# DESC: Main control flow
# ARGS: $@ (optional): Arguments provided to the script
# OUTS: None
# RETS: None
function main() {
    trap script_trap_err ERR
    trap script_trap_exit EXIT

    script_init "$@"
    parse_params "$@"
    cron_init
    colour_init
    #lock_init system

    run_custodian_policies
    run_custodian_mailer
}

# shellcheck source=source.sh
source "$(dirname "${BASH_SOURCE[0]}")/source.sh"

# Invoke main with args if not sourced
# Approach via: https://stackoverflow.com/a/28776166/8787985
if ! (return 0 2> /dev/null); then
    main "$@"
fi

# vim: syntax=sh cc=80 tw=79 ts=4 sw=4 sts=4 et sr
