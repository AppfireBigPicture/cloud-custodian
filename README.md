# Tagging Control documentation

![Static Badge](https://img.shields.io/badge/maintained-true-green)
![Static Badge](https://img.shields.io/badge/project_status-on_hold-yellow)

- **Project URL:** https://appfireteam.atlassian.net/wiki/spaces/EngOps/pages/97102462978/Tagging+Control
- **Project owner:** Juan Martin Pascale
- **Repository maintainer:** German Garces

## Project description

With Tagging Control, you can review cloud resources and receive notifications if they do not comply with predefined tag policies.

This project helps you enforce tagging standards across your cloud environment, ensuring consistency and compliance. Unlike manual audits, Tagging Control automates the review process, saving time and reducing errors.

## Who this project is for

This project is intended for cloud administrators, DevOps engineers, and IT managers who want to ensure compliance with tagging policies across their cloud resources. It helps users identify non-compliant resources and streamline the enforcement of tagging standards.

## Project dependencies

Before using Tagging Control, ensure you have the following prerequisites:

- **Docker**

  Required to containerize and run the application. [Install Docker](https://www.docker.com/).

- **Terraform 1.5.7 or higher**

  Required to manage infrastructure as code. [Install Terraform](https://developer.hashicorp.com/terraform/install).

- **Access to your cloud provider**

  Ensure you have permissions to create, delete and read resources to monitor.

- **Predefined tagging policies**

  A set of rules or standars for tags that the project will validate against.

- **Sensitive environment variables stored in SSM Parameter Store**

  Sensitive variables (e.g., Slack channel URL) must be stored securely in AWS SSM Parameter Store. Refer to `docker/entrypoint.sh` and `scripts/policy_generator.py` for the list of required variables.

- **Environment variables stored in Dockerfiles**

  Environment variables (e.g., AWS region, account ID) must be defined in the Dockerfile. Refer to `docker/Dockerfile` and `docker/Dockerfile-local` for the list of required variables.

- **Basic knowledge of Cloud Custodian**

  Familiarity with Cloud Custodian is recommended for understanding and managing resource compliance. [Learn more about Cloud Custodian](https://cloudcustodian.io/docs/index.html).

- **Read the full documentation**

  It is essential to read the full documentation in the [Additional Documentation](#additional-documentation) before deploying Tagging Control to ensure proper setup and usage.

## Instructions for using Tagging Control

Get started with Tagging Control by cloning the repository:

```bash
git clone https://github.com/fntkg/cloud-custodian.git
cd cloud-custodian
```

**Build the Docker image**

If building from a standard environment, use the `Dockerfile` located in the `docker/` directory:

```bash
docker build -t tagging-control -f docker/Dockerfile .
```

If building from Appfire's laptops, use the `Dockerfile-local` located in the `docker/` directory:

```bash
docker build -t tagging-control -f docker/Dockerfile-local .
```

**Configure tagging policies**

Tagging policies are defined in the `docker/scripts/policy_generator.py` script. Update this file to customize the tagging rules for your environment.

**Run tagging control**

Run the Docker container to start the application.

```bash
docker run tagging-control
```

### Troubleshoot Tagging Control

**Check logs**

View the container logs for debugging.

```bash
docker logs <container_id>
```

**Verify environment variables**

Ensure all required environment variables are correctly set.

**Other troubleshooting supports:**

* [How to Fix and Debug Docker Containers Like a Superhero](https://www.docker.com/blog/how-to-fix-and-debug-docker-containers-like-a-superhero/)
* [How to Debug & Troubleshoot Terraform Projects: Tutorial](https://spacelift.io/blog/terraform-debug)

## Additional documentation

For more information:

* [Infrastructure as Code overview diagram](./terraform/iac-overview.md)
* [Infrastructure as Code reference.](./terraform/reference.md)
* [Docker setup reference](./docker/README.md)

## How to get help

* Ask for support to project owner or repository maintainer.
* [Create a request in Global DevOps portal](https://appfireteam.atlassian.net/servicedesk/customer/portal/15)