#!/bin/bash

set -euo pipefail

c7n-org run --config accounts.yml --use policies/policy.yml --output-dir output
c7n-mailer --config mailer.yml --templates mailer-templates --run