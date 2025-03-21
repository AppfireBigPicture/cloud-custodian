# cloud-custodian-infra

This repo contains terraform code to deploy Cloud Custodian in AWS in a cost-effective way.

# AWS Infrastructure
## IAM Permissions

### Required Policies for All Roles

The following policies are required for roles to:

- Read, tag, and untag resources
- Send messages from an SQS queue

**Policies:**

- `ReadOnlyAccess`
- `ResourceGroupsandTagEditorFullAccess`
- `ResourceGroupsTaggingAPITagUntagSupportedResources`
- `CloudCustodianMailerClient` (self-managed)

**Trust Relationships:**

All roles must be assumable by the **CloudCustodian** role.

### Required Policies for CloudCustodian Role

The **CloudCustodian** role requires:

- `CloudCustodianMultiAccount` (self-managed)
- `CloudCustodianMailerAdmin` (self-managed)

**Trust Relationships:**

To analyze the account where **CloudCustodian** is deployed, the role must be assumable by itself.

CloudCustodian must be able to assume this role. For example, in EKS, a service account was created and linked to the job with permissions to assume the role.

### Self Managed Policies
#### CloudCustodianMultiAccount Policy

This policy allows the role to assume roles in other accounts.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::211125726674:role/AppfireCloudCustodian",
        "arn:aws:iam::156041420045:role/AppfireCloudCustodian"
      ]
    }
  ]
}
```

#### CloudCustodianMailerClient Policy

This policy allows roles to send and receive messages from the SQS queue.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudCustodianSendMessage",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-2:891377226793:cloudcustodian-mailer"
    }
  ]
}
```

#### CloudCustodianMailerAdmin Policy

This policy allows to retrieve and delete messages from an SQS Queue.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudCustodianSendMessage",
      "Effect": "Allow",
      "Action": [
        "sqs:DeleteMessage",
        "sqs:ReceiveMessage",
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-2:891377226793:cloudcustodian-mailer"
    }
  ]
}
```

## Deployment on AWS (Optimized Cost Architecture)

#### Overview

This architecture allows periodic execution of **Cloud Custodian** while minimizing costs by keeping the EC2 instance off when not in use.

#todo Add SQS Queue

### Architecture Diagram

```
┌───────────────────────────────┐  
│ EventBridge Scheduler         │  
└───────────────┬───────────────┘  
                │  
                ▼  
┌───────────────────────────────┐  
│ Lambda (Start EC2)            │  
└───────────────┬───────────────┘  
                │  
                ▼  
┌────────────────────────────────────────┐  
│ EC2 Instance                           │  
│ - Runs cloud custodian at startup      │  
│ - Shuts down after execution           │  
└───────────────┬────────────────────────┘  
                │  
                ▼  
┌───────────────────────────────┐  
│ Executes Custodian            │  
└───────────────────────────────┘  
```

### Components & Workflow

1️⃣ **EventBridge Rule**

- Triggers the **Lambda function** at scheduled times.

2️⃣ **Lambda Function (Start EC2)**

- Calls `StartInstances` API to start the EC2 instance.

3️⃣ **EC2 Instance (Cloud Custodian with Docker)**

- On startup, the **EC2** instance executes the **Docker container** running Cloud Custodian.
- **Docker** will pull the image (from DockerHub or ECR) and run Cloud Custodian.
- Shuts down after execution

### Benefits

✅ **Cost-Effective** – EC2 is only running when needed.  
✅ **Automated** – No manual intervention required.

### Other options

- Fargate & ECS.

## Credentials Management

Cloud Custodian and the Docker image it relies on require the following credentials:

1. Credentials to pull the Docker image from any repository.
2. Slack webhook (sensitive information).
3. AWS credentials (if the deployment instance doesn't have them).

These credentials can be stored in **AWS Systems Manager Parameter Store**. **AWS Secrets Manager** is another option, but it's not cost-effective as we wouldn't use its full features.

# Cloud Custodian Management
## Container image

The Docker image will include everything needed to analyze policies in AWS accounts:

- List of accounts to analyze
- Policies to review
- Notification settings
- Notification templates
- Entrypoint script

## Accounts Management

Cloud Custodian retrieves the accounts to analyze from a file provided via parameters. There are two approaches to handling this file:

1. **Static File:** Generate the file once and maintain it as accounts change.
2. **Dynamic File:** Generate the file each time an analysis runs.

Since creating the list is not resource-intensive, I believe the dynamic approach is the better option.

## Policies Management

Cloud Custodian processes policies from a single file passed as a parameter. Managing all policies within one file makes maintenance complex and inefficient.

To address this, I propose developing a tool that generates the necessary policies based on specified resources and tags. Since policies follow a strict schema, this tool would be simple to implement.

This approach would greatly simplify resource and tag management, improving maintainability and efficiency.

## Credentials management

Cloud Custodian and the Docker image it relies on require the following credentials:

1. Credentials to pull the Docker image from any repository.
2. Slack webhook (sensitive information).
3. AWS credentials (if the deployment instance doesn't have them).

These credentials can be stored in **AWS Systems Manager Parameter Store**. **AWS Secrets Manager** is another option, but it's not cost-effective as we wouldn't use its full features.

## Slack templates

For each notification sent by Cloud Custodian, a template can be specified to format the messages. I propose creating three templates:

1. One for when a resource is **not compliant** and action is required.
2. One for when the resource is **compliant**.
3. One for when the resource has been **deleted** due to non-compliance over a specific period.# AWS Infrastructure
## IAM Permissions

### Required Policies for All Roles

The following policies are required for roles to:

- Read, tag, and untag resources
- Send messages from an SQS queue

**Policies:**

- `ReadOnlyAccess`
- `ResourceGroupsandTagEditorFullAccess`
- `ResourceGroupsTaggingAPITagUntagSupportedResources`
- `CloudCustodianMailerClient` (self-managed)

**Trust Relationships:**

All roles must be assumable by the **CloudCustodian** role.

### Required Policies for CloudCustodian Role

The **CloudCustodian** role requires:

- `CloudCustodianMultiAccount` (self-managed)
- `CloudCustodianMailerAdmin` (self-managed)

**Trust Relationships:**

To analyze the account where **CloudCustodian** is deployed, the role must be assumable by itself.

CloudCustodian must be able to assume this role. For example, in EKS, a service account was created and linked to the job with permissions to assume the role.

### Self Managed Policies
#### CloudCustodianMultiAccount Policy

This policy allows the role to assume roles in other accounts.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": [
        "arn:aws:iam::211125726674:role/AppfireCloudCustodian",
        "arn:aws:iam::156041420045:role/AppfireCloudCustodian"
      ]
    }
  ]
}
```

#### CloudCustodianMailerClient Policy

This policy allows roles to send and receive messages from the SQS queue.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudCustodianSendMessage",
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-2:891377226793:cloudcustodian-mailer"
    }
  ]
}
```

#### CloudCustodianMailerAdmin Policy

This policy allows to retrieve and delete messages from an SQS Queue.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudCustodianSendMessage",
      "Effect": "Allow",
      "Action": [
        "sqs:DeleteMessage",
        "sqs:ReceiveMessage",
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-2:891377226793:cloudcustodian-mailer"
    }
  ]
}
```

## Deployment on AWS (Optimized Cost Architecture)

#### Overview

This architecture allows periodic execution of **Cloud Custodian** while minimizing costs by keeping the EC2 instance off when not in use.

#todo Add SQS Queue

### Architecture Diagram

```
┌───────────────────────────────┐  
│ EventBridge Scheduler         │  
└───────────────┬───────────────┘  
                │  
                ▼  
┌───────────────────────────────┐  
│ Lambda (Start EC2)            │  
└───────────────┬───────────────┘  
                │  
                ▼  
┌────────────────────────────────────────┐  
│ EC2 Instance                           │  
│ - Runs cloud custodian at startup      │  
│ - Shuts down after execution           │  
└───────────────┬────────────────────────┘  
                │  
                ▼  
┌───────────────────────────────┐  
│ Executes Custodian            │  
└───────────────────────────────┘  
```

### Components & Workflow

1️⃣ **EventBridge Rule**

- Triggers the **Lambda function** at scheduled times.

2️⃣ **Lambda Function (Start EC2)**

- Calls `StartInstances` API to start the EC2 instance.

3️⃣ **EC2 Instance (Cloud Custodian with Docker)**

- On startup, the **EC2** instance executes the **Docker container** running Cloud Custodian.
- **Docker** will pull the image (from DockerHub or ECR) and run Cloud Custodian.
- Shuts down after execution

### Benefits

✅ **Cost-Effective** – EC2 is only running when needed.  
✅ **Automated** – No manual intervention required.

### Other options

- Fargate & ECS.

## Credentials Management

Cloud Custodian and the Docker image it relies on require the following credentials:

1. Credentials to pull the Docker image from any repository.
2. Slack webhook (sensitive information).
3. AWS credentials (if the deployment instance doesn't have them).

These credentials can be stored in **AWS Systems Manager Parameter Store**. **AWS Secrets Manager** is another option, but it's not cost-effective as we wouldn't use its full features.

# Cloud Custodian Management
## Container image

The Docker image will include everything needed to analyze policies in AWS accounts:

- List of accounts to analyze
- Policies to review
- Notification settings
- Notification templates
- Entrypoint script

## Accounts Management

Cloud Custodian retrieves the accounts to analyze from a file provided via parameters. There are two approaches to handling this file:

1. **Static File:** Generate the file once and maintain it as accounts change.
2. **Dynamic File:** Generate the file each time an analysis runs.

Since creating the list is not resource-intensive, I believe the dynamic approach is the better option.

## Policies Management

Cloud Custodian processes policies from a single file passed as a parameter. Managing all policies within one file makes maintenance complex and inefficient.

To address this, I propose developing a tool that generates the necessary policies based on specified resources and tags. Since policies follow a strict schema, this tool would be simple to implement.

This approach would greatly simplify resource and tag management, improving maintainability and efficiency.

## Credentials management

Cloud Custodian and the Docker image it relies on require the following credentials:

1. Credentials to pull the Docker image from any repository.
2. Slack webhook (sensitive information).
3. AWS credentials (if the deployment instance doesn't have them).

These credentials can be stored in **AWS Systems Manager Parameter Store**. **AWS Secrets Manager** is another option, but it's not cost-effective as we wouldn't use its full features.

## Slack templates

For each notification sent by Cloud Custodian, a template can be specified to format the messages. I propose creating three templates:

1. One for when a resource is **not compliant** and action is required.
2. One for when the resource is **compliant**.
3. One for when the resource has been **deleted** due to non-compliance over a specific period.

# Repository Structure

```
/cloud-custodian
├── README.md
├── docker
│   ├── Dockerfile
│   ├── Dockerfile-local
│   ├── README.md
│   ├── config
│   │   ├── config.yaml.template
│   │   └── requirements.txt
│   ├── entrypoint.sh
│   ├── netskope-cert-bundle.pem
│   └── scripts
│       ├── c7n-pipeline.sh
│       └── policy_generator.py
└── terraform
    ├── README.md
    ├── lambda.js
    ├── lambda.zip
    ├── main.tf
    ├── modules
    │   ├── c7n
    │   │   ├── main.tf
    │   │   ├── outputs.tf
    │   │   └── variables.tf
    │   └── deployment
    │       ├── main.tf
    │       ├── outputs.tf
    │       └── variables.tf
    ├── providers.tf
    └── variables.tf
```

## TODO

- [ ] Discuss about Accounts Management. If dynamic, develop a script that creates the list. Here is something we may use: https://cloudcustodian.io/docs/tools/c7n-org.html#config-file-generation
- [ ] Discuss where to push Docker Image. Dockerhub/ECR...
- [ ] Discuss where to deploy this. I think it should be in its own account or in a "whole org management account".
- [ ] Test terraform code.
- [ ] Create Slack app.
- [ ] Upload sensitive information to AWS SSM Param in the proper account.
  - (If needed) Dockerhub creds
  - Slack Webhook Url