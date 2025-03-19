# Cloud Custodian Docker Setup

This folder provides all the necessary Docker configurations, dependencies, and scripts to run Cloud Custodian (c7n) in a containerized environment.

## Folder Structure

- **config/**
  - Contains configuration files for Cloud Custodian.
- **scripts/**
  - Contains scripts to handle tasks such as creating policies and launching the pipeline for **c7n-org** and **c7n-mailer**.
- `Dockerfile`: Main Dockerfile containing non-sensitive environment variables.
- `Dockerfile-local`: Used for deployments from machines with Netskope installed. This file leverages the `netskope-cert-bundle.pem` certificate.

## Environment Variables

- **Non-sensitive variables**: Defined directly in the Dockerfile.
- **Sensitive variables**: Such as the Slack webhook, are stored in the SSM Parameter Store (via the CloudCustodian app) and are retrieved by `entrypoint.sh` and `scripts/policy_generator.py`.

## GitHub Actions

A GitHub Action is set up to:
- Validate the Dockerfile using Hadolint.
- Build the Docker image.
- *(Future enhancement: Push the built image to a repository.)*

## Execution Flow

1. The execution starts with `entrypoint.sh`, which downloads sensitive environment variables from the SSM Parameter Store and prepares the environment for Cloud Custodian execution.
2. After the `entrypoint.sh` script runs, the default command executed is `c7n-pipeline.sh`. However, this can be overridden when running the Docker image.

Example to override the default command:
```bash
docker run your-docker-image /path/to/custom-script.sh
```

This allows you to run custom scripts or modify the execution pipeline as needed.