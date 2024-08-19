from django.conf import settings

from . import base


class QuicksightService(base.AWSService):
    aws_service_name = "quicksight"

    def get_embed_url(self, user):
        user_arn = self.arn(resource=f"user/default/{user.email}")
        response = self._request(
            "generate_embed_url_for_registered_user",
            AwsAccountId=self.account_id,
            UserArn=user_arn,
            ExperienceConfiguration={
                "QuickSightConsole": {
                    "InitialPath": "/start",
                    "FeatureConfigurations": {"StatePersistence": {"Enabled": True}},
                },
            },
            AllowedDomains=settings.QUICKSIGHT_DOMAINS,
        )
        if response:
            return response["EmbedUrl"]

        return response
