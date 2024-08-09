from django.conf import settings

import botocore
import sentry_sdk

from ap.aws import base


class QuicksightAWSService(base.AWSService):
    @property
    def client(self):
        return self.boto3_session.client("quicksight")

    def get_embed_url(self, user):
        try:
            response = self.client.generate_embed_url_for_registered_user(
                AwsAccountId=settings.COMPUTE_ACCOUNT_ID,
                UserArn=user.quicksight_arn,
                ExperienceConfiguration={
                    "QuickSightConsole": {
                        "InitialPath": "/start",
                        "FeatureConfigurations": {"StatePersistence": {"Enabled": True}},
                    },
                },
                AllowedDomains=settings.QUICKSIGHT_DOMAINS,
            )
            url = response["EmbedUrl"]
        except botocore.exceptions.ClientError as e:
            if settings.DEBUG:
                raise e
            sentry_sdk.capture_exception(e)
            url = None

        return url
