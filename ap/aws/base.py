from django.conf import settings

import boto3

from ap.aws import session


class AWSService:
    def __init__(self, assume_role_name=None, profile_name=None, region_name=None):
        self.assume_role_name = assume_role_name or settings.DEFAULT_ROLE_ARN
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
            session_name=self.__class__.__name__,
        )

    @property
    def name(self):
        return self.__class__.__name__
