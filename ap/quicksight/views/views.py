from django.conf import settings
from django.views.generic import TemplateView

import boto3

from ap.auth.views.mixins import OIDCLoginRequiredMixin


class QuicksightView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "quicksight.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = context["view"].request.user
        context["embed_url"] = self._get_embed_url(user)
        return context

    def _get_embed_url(self, user):
        qs_session_name = "quicksight-test"

        sts = boto3.client("sts")
        response = sts.assume_role(
            RoleArn=f"arn:aws:iam::{settings.COMPUTE_ACCOUNT_ID}:role/quicksight_test",
            RoleSessionName=qs_session_name,
        )

        qs_credentials = {
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "aws_session_token": response["Credentials"]["SessionToken"],
        }

        quicksight = boto3.client("quicksight", **qs_credentials, region_name="eu-west-2")

        # Gets information about members of the aws_analytical_platform group
        # group_response = quicksight.list_group_memberships(GroupName="aws_analytical_platform",
        #                                     AwsAccountId=settings.COMPUTE_ACCOUNT_ID,
        #                                     Namespace="default")
        # print(group_response)

        # Assumes email is part of the above group
        user_response = quicksight.describe_user(
            UserName=user.email, AwsAccountId=settings.COMPUTE_ACCOUNT_ID, Namespace="default"
        )
        print(user_response)

        url_response = quicksight.generate_embed_url_for_registered_user(
            AwsAccountId=settings.COMPUTE_ACCOUNT_ID,
            UserArn=user_response["User"]["Arn"],
            ExperienceConfiguration={
                "QuickSightConsole": {
                    "InitialPath": "/start",
                    "FeatureConfigurations": {"StatePersistence": {"Enabled": True}},
                },
            },
            AllowedDomains=["http://localhost:8000"],
        )

        return url_response["EmbedUrl"]
