import yaml
import boto3
import os
from typing import List, Dict

class Policy:
    def __init__(self, resource: str, tags: list, delete_action=None):
        self.resource = resource
        self.tags = tags
        self.delete_action = delete_action
        self.c7n_tag = "tag:custodian_cleanup"
        self._get_params() # Get sensitive params

    def _get_params(self):
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION"))
        self.queue_arn = ssm.get_parameter(Name="/c7n/queue_arn", WithDecryption=True)["Parameter"]["Value"]
        self.slack_webhook_url = ssm.get_parameter(Name="/c7n/slack_webhook_url", WithDecryption=True)["Parameter"]["Value"]

    def generate(self) -> list:
        tag_compliance_filters = [{"tag:" + tag: "absent"} for tag in self.tags]

        if not self.delete_action:
            return [
                {
                    "name": f"{self.resource}-mark",
                    "resource": self.resource,
                    "comment": "Find all resources that are not conformant to tagging policies, and tag them for deletion in 4 days.",
                    "filters": [
                        {self.c7n_tag: "absent"},
                        {"or": tag_compliance_filters}
                    ],
                    "actions": [
                        {
                            "type": "notify",
                            "slack_template": "slack",
                            "slack_msg_color": "warning",
                            "to": [self.slack_webhook_url],
                            "violation_desc": "Tags missing in the following resources. These resources will be deleted if they are not conformant to tagging policies.",
                            "action_desc": "Tags resources accordingly. Ask DevOps team for help.",
                            "transport": {
                                "type": "sqs",
                                "queue": self.queue_arn
                            }
                        }
                    ]
                }
            ]

        return [
            {
                "name": f"{self.resource}-mark",
                "resource": self.resource,
                "comment": "Find all resources that are not conformant to tagging policies, and tag them for deletion in 4 days.",
                "filters": [
                    {self.c7n_tag: "absent"},
                    {"or": tag_compliance_filters}
                ],
                "actions": [
                    {"type": "mark-for-op", "tag": self.c7n_tag, "op": self.delete_action, "days": 4},
                    {
                        "type": "notify",
                        "slack_template": "slack",
                        "slack_msg_color": "warning",
                        "to": [self.slack_webhook_url],
                        "violation_desc": "Tags missing in the following resources.",
                        "action_desc": "Tags resources accordingly. Ask DevOps team for help.",
                        "transport": {
                            "type": "sqs",
                            "queue": self.queue_arn
                        }
                    }
                ]
            },
            {
                "name": f"{self.resource}-unmark",
                "resource": self.resource,
                "comment": "Any resource which have previously been marked as non compliant with tag policies, that are now compliant should be unmarked as non-compliant.",
                "filters": (
                    [{"tag:custodian_cleanup": "not-null"}] +
                    [{"tag:" + tag: "not-null"} for tag in self.tags]
                ),
                "actions": [
                    {"type": "remove-tag", "tags": ["custodian_cleanup"]},
                    {
                        "type": "notify",
                        "slack_template": "slack",
                        "slack_msg_color": "good",
                        "to": [self.slack_webhook_url],
                        "violation_desc": "Your resource is now compliant.",
                        "action_desc": "You can breathe easy now.",
                        "transport": {
                            "type": "sqs",
                            "queue": self.queue_arn
                        }
                    }
                ]
            },
            {
                "name": f"{self.resource}-delete",
                "resource": self.resource,
                "comment": "Delete all resources previously marked for deletion by today's date. Also verify that they continue to not meet tagging policies.",
                "filters": [
                    {"type": "marked-for-op", "tag": "custodian_cleanup", "op": self.delete_action},
                    {"or": tag_compliance_filters}
                ],
                "actions": [
                    {"type": self.delete_action},
                    {
                        "type": "notify",
                        "slack_template": "slack",
                        "slack_msg_color": "danger",
                        "to": [self.slack_webhook_url],
                        "violation_desc": "Tags missing in the resources for 4 days.",
                        "action_desc": "The resources have been deleted.",
                        "transport": {
                            "type": "sqs",
                            "queue": self.queue_arn
                        }
                    }
                ]
            }
        ]


def generate_policies(resources_tags_dict: Dict[str, Dict[str, List[str]]]) -> Dict:
    policies_list = []

    for resource, config in resources_tags_dict.items():
        tags = config.get("tags", [])
        delete_action = config.get("delete_action", None)
        policy = Policy(resource=resource, tags=tags, delete_action=delete_action)
        policies_list.extend(policy.generate())

    return {"policies": policies_list}

if __name__ == "__main__":
    # For resources and possible actions: https://cloudcustodian.io/docs/aws/resources
    # If not suitable action, don't add the `delete_action` key.
    resources_tags = {
        # Compute
        "ec2": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "EndpointType"], "delete_action": "terminate"},
        "ec2-spot-fleet-request": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "EndpointType"]},
        "ec2-capacity-reservation": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},
        "ami": {"tags": ["DeploymentType", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "deregister"},
        "lambda": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "elasticbeanstalk-environment": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "terminate"},
        "batch-compute": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]  , "delete_action": "delete"},
        "workspaces": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "terminate"},

        # Containers & Kubernetes
        "ecs": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},
        "ecs-task-definition": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "ecs-task": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "stop"},
        "ecs-service": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "ecs-container-instance": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},
        "eks": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "eks-nodegroup": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},
        "ecr": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},
        "ecr-image": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg"]},

        # Storage
        "ebs": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "ebs-snapshot": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "s3": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "efs": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "glacier": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "backup-plan": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"]},
        "backup-vault": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"]},

        # Networking & Content Delivery
        "vpc": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "subnet": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory"]},
        "security-group": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory"], "delete_action": "delete"},
        "route-table": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory"]},
        "internet-gateway": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "nat-gateway": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "elastic-ip": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "disassociate"},
        "elb": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "app-elb": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "app-elb-target-group": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "globalaccelerator": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "distribution": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "disable"},
        "rest-api": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "apigwv2": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "firewall": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "waf": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "waf-regional": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "wafv2": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "shield-protection": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "network-acl": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "peering-connection": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "vpn-gateway": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "r53domain": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "hostedzone": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "prefix-list": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "directconnect": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},

        # Database
        "rds": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "rds-cluster": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "rds-cluster-snapshot": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "rds-snapshot": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "dynamodb-table": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "redshift": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "cache-cluster": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},

        # Security, Identity, & Compliance
        "iam-role": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "iam-policy": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "iam-user": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "acm-certificate": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "config-rule": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "cloudtrail": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "iam-saml-provider": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "iam-certificate": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "iam-oidc-provider": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "kms-key": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "guardduty-finding": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "ses-email-identity": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "identity-pool": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "user-pool": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},

        # Management & Governance
        "cfn": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},
        "ssm-document": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "log-group": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "alarm": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "catalog-product": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"]},

        # Machine Learning
        "sagemaker-notebook": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "sagemaker-model": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},

        # Developer Tools
        "codebuild": {"tags": ["DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "codepipeline": {"tags": ["DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "codedeploy-app": {"tags": ["DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},
        "codecommit": {"tags": ["DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg"], "delete_action": "delete"},

        # Analytics
        "athena-work-group": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"]},
        "glue-crawler": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "glue-database": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"]},
        "glue-job": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "kinesis": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "Exposure", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},

        # Integration & Messaging
        "sns": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "sqs": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "firehose": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg", "DataClassification"], "delete_action": "delete"},
        "step-machine": {"tags": ["Environment", "DeploymentType", "Brand", "AppCategory", "AdminEmail", "OwningOrg", "DataClassification"]},
    }

    policies = generate_policies(resources_tags)
    with open("docker/policies.yml", "w") as f:
        yaml.dump(policies, f, sort_keys=False, default_flow_style=False)