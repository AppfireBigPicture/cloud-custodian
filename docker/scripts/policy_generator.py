import os
import yaml
import boto3
from typing import List, Dict, Any, Optional


class Policy:
    """
    Represents a policy for an AWS resource that checks tag compliance,
    sends notifications, and optionally marks resources for deletion.
    """

    def __init__(self, resource: str, tags: List[str], delete_action: Optional[str] = None) -> None:
        """
        Initialize the Policy.

        Args:
           resource (str): The name of the AWS resource.
           tags (List[str]): List of required tag keys.
           delete_action (Optional[str]): Action to perform for deletion, if applicable.
         """
        self.resource = resource
        self.tags = tags
        self.delete_action = delete_action
        self.custodian_tag = "tag:custodian_cleanup"
        self._load_sensitive_params()

    def _load_sensitive_params(self) -> None:
        """
        Load sensitive parameters such as the SQS queue ARN and Slack webhook URL from AWS SSM.
        """
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION"))
        self.queue_arn = self._get_ssm_parameter(ssm, "/c7n/queue_arn")
        self.slack_webhook_url = self._get_ssm_parameter(ssm, "/c7n/slack_webhook_url")

    @staticmethod
    def _get_ssm_parameter(ssm_client: Any, name: str) -> str:
        """
        Retrieve a parameter value from AWS SSM Parameter Store.

        Args:
            ssm_client (Any): A boto3 SSM client.
            name (str): The name of the parameter.

        Returns:
            str: The decrypted parameter value.
        """
        return ssm_client.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

    def _build_notify_action(self, template: str, color: str, violation_desc: str, action_desc: str) -> Dict[str, Any]:
        """
        Build a notification action dictionary.

        Args:
            template (str): The Slack template to use.
            color (str): The color indicator for the Slack message.
            violation_desc (str): Description of the violation.
            action_desc (str): Description of the action taken.

        Returns:
            Dict[str, Any]: A dictionary representing the notification action.
        """
        return {
            "type": "notify",
            "slack_template": template,
            "slack_msg_color": color,
            "to": [self.slack_webhook_url],
            "violation_desc": violation_desc,
            "action_desc": action_desc,
            "transport": {"type": "sqs", "queue": self.queue_arn},
        }

    def _generate_tag_filters(self) -> List[Dict[str, str]]:
        """
        Generate a list of tag compliance filters based on the required tags.

        Returns:
            List[Dict[str, str]]: List of tag filter dictionaries.
        """
        return [{"tag:" + tag: "absent"} for tag in self.tags]

    def generate(self) -> List[Dict[str, Any]]:
        """
        Generate a list of policy dictionaries based on tag compliance and optional delete action.

        Returns:
            List[Dict[str, Any]]: List of policies.
        """
        tag_filters = self._generate_tag_filters()
        common_filters = [
            {self.custodian_tag: "absent"},
            {"or": tag_filters},
        ]
        _policies = []

        if self.delete_action:
            # Policy for marking resources for deletion with a delete action.
            _policies.append({
                "name": f"{self.resource}-mark",
                "resource": self.resource,
                "comment": (
                    "Find all resources that are not conformant to tagging policies, "
                    "and tag them for deletion in 4 days."
                ),
                "filters": common_filters,
                "actions": [
                    {"type": "mark-for-op", "tag": self.custodian_tag, "op": self.delete_action, "days": 4},
                    self._build_notify_action(
                        template="slack",
                        color="warning",
                        violation_desc="Tags missing in the following resources.",
                        action_desc="Tags resources accordingly. Ask DevOps team for help."
                    ),
                ],
            })

            # Policy for unmarking resources that have become compliant.
            unmark_filters = (
                [{"tag:custodian_cleanup": "not-null"}] +
                [{"tag:" + tag: "not-null"} for tag in self.tags]
            )
            _policies.append({
                "name": f"{self.resource}-unmark",
                "resource": self.resource,
                "comment": (
                    "Any resource which has previously been marked as non compliant with tag policies, "
                    "that is now compliant should be unmarked."
                ),
                "filters": unmark_filters,
                "actions": [
                    {"type": "remove-tag", "tags": ["custodian_cleanup"]},
                    self._build_notify_action(
                        template="slack",
                        color="good",
                        violation_desc="Your resource is now compliant.",
                        action_desc="You can breathe easy now."
                    ),
                ],
            })

            # Policy for deleting resources that are marked for deletion.
            _policies.append({
                "name": f"{self.resource}-delete",
                "resource": self.resource,
                "comment": (
                    "Delete all resources previously marked for deletion by today's date. "
                    "Also verify that they continue to not meet tagging policies."
                ),
                "filters": [
                    {"type": "marked-for-op", "tag": "custodian_cleanup", "op": self.delete_action},
                    {"or": tag_filters},
                ],
                "actions": [
                    {"type": self.delete_action},
                    self._build_notify_action(
                        template="slack",
                        color="danger",
                        violation_desc="Tags missing in the resources for 4 days.",
                        action_desc="The resources have been deleted."
                    ),
                ],
            })
        else:
            # Policy for notifying resources without a delete action.
            _policies.append({
                "name": f"{self.resource}-mark",
                "resource": self.resource,
                "comment": (
                    "Find all resources that are not conformant to tagging policies, "
                    "and tag them for deletion in 4 days."
                ),
                "filters": common_filters,
                "actions": [
                    self._build_notify_action(
                        template="slack",
                        color="warning",
                        violation_desc=(
                            "Tags missing in the following resources. "
                            "These resources will be deleted if they are not conformant to tagging policies."
                        ),
                        action_desc="Tags resources accordingly. Ask DevOps team for help."
                    )
                ],
            })

        return _policies


def generate_policies(resources_tags_dict: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
    """
    Generate policies for each AWS resource based on provided tag configuration.

    Args:
        resources_tags_dict (Dict[str, Dict[str, List[str]]]): Dictionary mapping resource names
            to their configuration, including required tags and optional delete actions.

    Returns:
        Dict[str, Any]: A dictionary with a single key "policies" containing a list of policy definitions.
    """
    policies_list = []
    for resource, config in resources_tags_dict.items():
        tags = config.get("tags", [])
        delete_action = config.get("delete_action")
        policy = Policy(resource=resource, tags=tags, delete_action=delete_action)
        policies_list.extend(policy.generate())
    return {"policies": policies_list}


if __name__ == "__main__":
    # Define resource configurations including required tags and optional delete actions.
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

    # Generate policies and write them to a YAML file.
    policies = generate_policies(resources_tags)
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "policies.yml")
    with open(output_path, "w") as file:
        yaml.dump(policies, file, sort_keys=False, default_flow_style=False)
