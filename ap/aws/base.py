from django.conf import settings

import boto3
import structlog
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session

log = structlog.getLogger(__name__)

TTL = 1500


class AWSCredentials:
    def __init__(self, assume_role_name=None, region_name=None, profile_name=None) -> None:
        self.assume_role_name = assume_role_name or settings.DEFAULT_ROLE_ARN
        self.region_name = region_name or settings.AWS_DEFAULT_REGION
        self.profile_name = profile_name

    def get_sts_credentials(self):
        log.info("Getting AWS credentials using STS")
        boto3_ini_session = boto3.Session(region_name=self.region_name)
        sts = boto3_ini_session.client("sts")
        response = sts.assume_role(
            RoleArn=self.assume_role_name,
            RoleSessionName="assume-test-session",
            DurationSeconds=TTL,
        )
        return {
            "access_key": response["Credentials"]["AccessKeyId"],
            "secret_key": response["Credentials"]["SecretAccessKey"],
            "token": response["Credentials"]["SessionToken"],
            "expiry_time": response["Credentials"]["Expiration"].isoformat(),
        }

    def get_default_credentials(self):
        log.info("Using default AWS credentials")
        boto3_ini_session = boto3.Session(
            region_name=self.region_name, profile_name=self.profile_name
        )
        return boto3_ini_session.get_credentials()

    def refreshable_credentials(self):
        log.info("Refreshing AWS credentials")
        if not self.assume_role_name:
            return self.get_default_credentials()

        return RefreshableCredentials.create_from_metadata(
            metadata=self.get_sts_credentials(),
            refresh_using=self.get_sts_credentials,
            method="sts-assume-role",
        )


class AWSService:
    _boto3_session = None
    _credentials = None

    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        self.assume_role_name = assume_role_name or settings.DEFAULT_ROLE_ARN
        self.profile_name = profile_name
        self.region_name = region_name or settings.AWS_DEFAULT_REGION

    @property
    def credentials(self):
        if self._credentials is not None:
            return self._credentials

        self._credentials = AWSCredentials(
            assume_role_name=self.assume_role_name,
            region_name=self.region_name,
            profile_name=self.profile_name,
        ).refreshable_credentials()

        return self._credentials

    @property
    def boto3_session(self):
        if self._boto3_session is not None:
            return self._boto3_session

        botocore_session = get_session()
        botocore_session.set_config_variable("region", self.region_name)
        botocore_session._credentials = self.credentials
        self._boto3_session = boto3.Session(botocore_session=botocore_session)

        return self._boto3_session
