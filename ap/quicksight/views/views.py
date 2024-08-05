from django.conf import settings
from django.views.generic import TemplateView

import boto3
import botocore
import sentry_sdk

from ap.auth.views.mixins import OIDCLoginRequiredMixin


class QuicksightView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "quicksight.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["embed_url"] = self._get_embed_url(user=self.request.user)
        return context

    def _get_embed_url(self, user):
        sts = boto3.client("sts")
        # TODO update as neccessary. This is a temporary solution as our local roles dont have
        # quicksight permissions. If we update the app to use a role both locally and in dev/prod
        # this assume_role call will not be necessary
        response = sts.assume_role(
            RoleArn=f"arn:aws:iam::{settings.COMPUTE_ACCOUNT_ID}:role/quicksight_test",
            RoleSessionName=f"quicksight-session-{user.email}",
        )
        qs_credentials = {
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "aws_session_token": response["Credentials"]["SessionToken"],
        }

        try:
            quicksight = boto3.client("quicksight", **qs_credentials, region_name="eu-west-2")
            url_response = quicksight.generate_embed_url_for_registered_user(
                AwsAccountId=settings.COMPUTE_ACCOUNT_ID,
                UserArn=self.request.user.quicksight_arn,
                ExperienceConfiguration={
                    "QuickSightConsole": {
                        "InitialPath": "/start",
                        "FeatureConfigurations": {"StatePersistence": {"Enabled": True}},
                    },
                },
                AllowedDomains=settings.QUICKSIGHT_DOMAINS,
            )
            url = url_response["EmbedUrl"]
        except botocore.exceptions.ClientError as e:
            sentry_sdk.capture_exception(e)
            url = None

        return url
