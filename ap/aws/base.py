from functools import cached_property

from django.conf import settings

import boto3
import botocore
import sentry_sdk

from . import session


class AWSService:
    IAM = "iam"
    S3 = "s3"
    REGIONLESS_SERVICES = [IAM, S3]
    aws_service_name: str = ""

    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        self.assume_role_name = assume_role_name
        self.profile_name = profile_name
        self.region_name = region_name or settings.AWS_DEFAULT_REGION

    @property
    def credential_session_set(self) -> session.AWSCredentialSessionSet:
        return session.AWSCredentialSessionSet()

    @property
    def boto3_session(self) -> boto3.Session:
        return self.credential_session_set.get_or_create_session(
            profile_name=self.profile_name,
            assume_role_name=self.assume_role_name,
            region_name=self.region_name,
        )

    @property
    def client(self):
        return self.boto3_session.client(self.aws_service_name)

    @cached_property
    def account_id(self):
        """
        Get the account ID from STS
        """
        return self.boto3_session.client("sts").get_caller_identity()["Account"]

    def arn(self, resource, service="", region_name="", account_id=""):
        service = service or self.aws_service_name
        region_name = region_name or self.region_name
        account_id = account_id or self.account_id

        if service in self.REGIONLESS_SERVICES:
            region_name = ""

        return f"arn:aws:{service}:{region_name}:{account_id}:{resource}"

    def _request(self, method_name, **kwargs):
        """
        Make a request to the AWS service client. Handles exceptions and logs them to Sentry.
        """
        try:
            return getattr(self.client, method_name)(**kwargs)
        except botocore.exceptions.ClientError as e:
            if settings.DEBUG:
                raise e
            sentry_sdk.capture_exception(e)
            return None
