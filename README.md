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

- **Familiarity with Cloud Custodian**  
  You should understand Cloud Custodian policies, filters, and actions to author or customize your own tagging rules.  
  – Docs: https://cloudcustodian.io/docs/index.html

- **Docker**  
  Used to build and run the `c7n-image` container that executes policies (`c7n-pipeline.sh`), mailer, and org-wide scans.  
  – Install Docker: https://docs.docker.com/get-docker/  

- **Terraform (v1.0+)**  
  Manages the AWS infrastructure: EventBridge rules, Lambda, EC2 instances, IAM roles, SQS queues, and SSM parameters.  
  – Install: https://learn.hashicorp.com/tutorials/terraform/install-cli  
  – AWS provider docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

- **AWS CLI & AWS IAM Permissions**  
  Required to bootstrap SSM Parameter Store entries, deploy Terraform, and manage IAM roles/policies.  
  – Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html  
  – You’ll need at minimum:
  ```
  ReadOnlyAccess
  ResourceGroupsandTagEditorFullAccess
  ResourceGroupsTaggingAPITagUntagSupportedResources
  CloudCustodianMailerClient (self-managed)
  CloudCustodianMultiAccount (self-managed)
  CloudCustodianMailerAdmin (self-managed)  
  ```  
  See full permissions in [terraform/reference.md](./terraform/README.md).

- **AWS SSM Parameter Store**  
  Stores sensitive values (Slack webhook URL, Docker pull credentials, AWS keys). The container’s `entrypoint.sh` fetches these at runtime.  
  – Guide: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

- **Slack Webhook**  
  For compliance notifications. Create an incoming-webhook in your Slack workspace, then store its URL in SSM Parameter Store.  
  – Setup: https://api.slack.com/messaging/webhooks

- **Account & Policies Files**
  - **Accounts file** (static or dynamically generated) listing AWS account IDs for multi-account runs.
  - **Policies manifest** describing which Cloud Custodian policies to apply.  
    You may choose to integrate a generator tool to produce per-resource or per-tag schemas at runtime.

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

* [Infrastructure as Code reference.](./terraform/README.md)
* [Architecture Overview (Discussion).](./terraform/architecture-overview-discussion.md)
* [Docker setup reference](./docker/README.md)

## How to get help

* Ask for support to project owner or repository maintainer.
* [Create a request in Global DevOps portal](https://appfireteam.atlassian.net/servicedesk/customer/portal/15)