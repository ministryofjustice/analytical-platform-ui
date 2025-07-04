import boto3
import structlog
from botocore import credentials
from botocore.session import get_session
from django.conf import settings

log = structlog.getLogger(__name__)

TTL = 1500


class BotoSession:
    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        self.assume_role_name = assume_role_name
        if self.assume_role_name is None and settings.DEFAULT_STS_ROLE_TO_ASSUME is not None:
            self.assume_role_name = settings.DEFAULT_STS_ROLE_TO_ASSUME

        self.region_name = region_name or settings.AWS_DEFAULT_REGION
        self.profile_name = profile_name

    def refreshable_credentials(self):
        log.info("Loading AWS credentials")
        if not self.assume_role_name:
            # boto3 refreshes the credentials automatically if no role is assumed
            return self.get_default_credentials()

        return credentials.RefreshableCredentials.create_from_metadata(
            metadata=self.get_sts_credentials(),
            refresh_using=self.get_sts_credentials,
            method="sts-assume-role",
        )

    def get_sts_credentials(self) -> dict:
        log.info("Getting credentials using STS")
        boto3_ini_session = boto3.Session(region_name=settings.AWS_DEFAULT_REGION)
        sts = boto3_ini_session.client("sts")
        response = sts.assume_role(
            RoleArn=self.assume_role_name,
            RoleSessionName=f"analytical-platform-ui-{settings.ENV}",
            DurationSeconds=TTL,
        )
        return {
            "access_key": response["Credentials"]["AccessKeyId"],
            "secret_key": response["Credentials"]["SecretAccessKey"],
            "token": response["Credentials"]["SessionToken"],
            "expiry_time": response["Credentials"]["Expiration"].isoformat(),
        }

    def get_default_credentials(self) -> credentials.Credentials:
        log.info("Getting credentials using default boto3 method")
        boto3_ini_session = boto3.Session(
            region_name=self.region_name, profile_name=self.profile_name
        )
        return boto3_ini_session.get_credentials()

    def get_boto3_session(self) -> boto3.Session:
        log.info("Creating a new boto3 session")
        botocore_session = get_session()
        botocore_session.set_config_variable("region", self.region_name)
        botocore_session._credentials = self.refreshable_credentials()
        return boto3.Session(botocore_session=botocore_session)


class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls in cls._instances:
            return cls._instances[cls]

        instance = super().__call__(*args, **kwargs)
        cls._instances[cls] = instance
        return instance


class AWSCredentialSessionSet(metaclass=SingletonMeta):
    def __init__(self):
        self.credential_sessions = {}

    def get_or_create_session(
        self,
        profile_name: str | None = None,
        assume_role_name: str | None = None,
        region_name: str | None = None,
    ) -> boto3.Session:
        credential_session_key = f"{profile_name}_{assume_role_name}_{region_name}"
        if credential_session_key in self.credential_sessions:
            log.info(f"Returning existing session for {credential_session_key}")
            return self.credential_sessions[credential_session_key]

        log.warn(f"(for monitoring purpose) Initialising session ({credential_session_key})")
        self.credential_sessions[credential_session_key] = BotoSession(
            region_name=region_name,
            profile_name=profile_name,
            assume_role_name=assume_role_name,
        ).get_boto3_session()
        return self.credential_sessions[credential_session_key]
