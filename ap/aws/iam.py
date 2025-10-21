import json

import botocore
import structlog
from django.conf import settings

from ap.aws.base import AWSService

logger = structlog.get_logger(__name__)


ROLE_POLICY_DOCUMENT = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "TrustRoleAndServiceToAssume",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::112639118718:role/aws-reserved/sso.amazonaws.com/eu-west-2/AWSReservedSSO_platform-engineer-admin_7e1fd24510fbc17b"  # noqa: E501
            },
            "Action": ["sts:TagSession", "sts:AssumeRole"],
        }
    ],
}


class IAMService(AWSService):
    aws_service_name = "iam"

    def __init__(self, catalog_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_id = catalog_id or self.account_id
        self.clients = {}

    def get_role(self, role_name):
        try:
            response = self.client.get_role(RoleName=role_name)
            return response.get("Role", {})
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                logger.warning(f"Role {role_name} does not exist.")
                raise e

    def create_role(self, role_name, assume_role_policy_document=None, description=""):
        try:
            assume_role_policy_document = assume_role_policy_document or ROLE_POLICY_DOCUMENT

            response = self.client.create_role(
                Path="/user/",
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
                Description=description,
            )
            return response.get("Role", {})
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error creating role {role_name}: {e}")
            raise e

    def attach_role_policy(self, role_name, policy_arn=""):
        try:
            policy_arn = policy_arn or settings.POC_USER_POLICY_ARN
            self.client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            logger.info(f"Attached policy {policy_arn} to role {role_name}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error attaching policy {policy_arn} to role {role_name}: {e}")
            raise e
