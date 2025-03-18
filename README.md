# cloud-custodian-infra
This repo contains terraform code to deploy Cloud Custodian in AWS in a cost-effective way.

## Repository Structure

```
/cloud-custodian-deployment  
│── /docker/                  # Docker image & related configs  
│   ├── Dockerfile  
│   ├── config/  
│   ├── scripts/  
│   ├── README.md  
│  
│── /terraform/                # AWS infra deployment  
│   ├── /main-infra/           # Core infra (Lambda, ECS, etc.)  
│   │   ├── main.tf  
│   │   ├── variables.tf  
│   │   ├── outputs.tf  
│   │   ├── README.md  
│   │  
│   ├── /custodian-infra/      # Cloud Custodian-specific infra (SQS, roles)  
│   │   ├── main.tf  
│   │   ├── variables.tf  
│   │   ├── outputs.tf  
│   │   ├── README.md  
│  
│── /terragrunt/               # Cross-account role management  
│   ├── /account-A/  
│   │   ├── terragrunt.hcl  
│   │   ├── roles.tf  
│   │   ├── policies.tf  
│   │   ├── README.md  
│   ├── /account-B/  
│   ├── /account-C/  
│  
│── /scripts/                  # Helper scripts (deployment, automation)  
│── /docs/                     # Documentation  
│── .github/                    # CI/CD workflows (GitHub Actions)  
│── README.md
```