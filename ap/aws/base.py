from django.conf import settings

import boto3
from botocore.session import get_session


class AWSService:
    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        self.assume_role_name = assume_role_name or settings.DEFAULT_ROLE_ARN
        self.profile_name = profile_name
        self.region_name = region_name or settings.AWS_DEFAULT_REGION

    def get_sts_credentials(self):
        boto3_ini_session = boto3.Session(region_name=self.region_name)
        sts = boto3_ini_session.client("sts")
        response = sts.assume_role(
            RoleArn=self.assume_role_name,
            RoleSessionName="assume-test-session",
        )
        return {
            "access_key": response["Credentials"]["AccessKeyId"],
            "secret_key": response["Credentials"]["SecretAccessKey"],
            "token": response["Credentials"]["SessionToken"],
        }

    def get_credentials(self):
        boto3_ini_session = boto3.Session(
            region_name=self.region_name, profile_name=self.profile_name
        )
        session_credentials = boto3_ini_session.get_credentials()
        return {
            "access_key": session_credentials.access_key,
            "secret_key": session_credentials.secret_key,
            "token": session_credentials.token,
        }

    @property
    def credentials(self):
        if self.assume_role_name:
            return self.get_sts_credentials()

        return self.get_credentials()

    @property
    def boto3_session(self):
        botocore_session = get_session()
        botocore_session.set_config_variable("region", self.region_name)
        botocore_session.set_credentials(**self.credentials)
        return boto3.Session(botocore_session=botocore_session)
