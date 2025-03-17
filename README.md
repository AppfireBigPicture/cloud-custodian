# cloud-custodian-infra
This repo contains terraform code to deploy Cloud Custodian in AWS in a cost-effective way.

**Notes:**
- TFLint
- terraform-docs
- Infracost
- Checkov


- **EventBridge Rule:** Set to run every 24 hours.  
- **Lambda Function:** Triggered by the rule, it starts an EC2 instance with a specific AMI and startup script.
## Architecture Design

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

## Requirements

- AWS account with appropriate permissions.
- Terraform (v0.12+).
- AWS CLI (optional, for verification).
- ZIP utility to package the Lambda function.

## Estructura del Proyecto