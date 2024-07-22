from django.conf import settings
from django.utils import timezone

import boto3
import botocore
import botocore.exceptions
import jwt
import structlog
from authlib.integrations.django_client import OAuth

from ap.users.models import User

logger = structlog.get_logger(__name__)

oauth = OAuth()
oauth.register(
    "azure",
    client_id=settings.AUTHLIB_OAUTH_CLIENTS["azure"]["client_id"],
    # client_secret is not needed for PKCE flow
    server_metadata_url=settings.AUTHLIB_OAUTH_CLIENTS["azure"]["server_metadata_url"],
    client_kwargs=settings.AUTHLIB_OAUTH_CLIENTS["azure"]["client_kwargs"],
)


class OIDCSubAuthenticationBackend:
    def __init__(self, token):
        self.token = token

    def filter_users_by_claims(self):
        user_id = self.token.get("userinfo", {}).get("oid")
        return User.objects.filter(pk=user_id).first()

    def _get_username(self, user_info):
        return user_info.get("username") or User.construct_username(user_info.get("name"))

    def _create_user(self):
        user_info = self.token.get("userinfo")
        return User.objects.create(
            pk=user_info.get("oid"),
            username=self._get_username(user_info),
            nickname=user_info.get("nickname", ""),
            email=user_info.get("email"),
            name=user_info.get("name", ""),
        )

    def _update_user(self, user):
        user_info = self.token.get("userinfo")
        # Update the non-key information to sync the user's info
        # with user profile from idp when the user's username is not changed.
        if user.username != self._get_username(user_info):
            return user

        if user.email != user_info.get("email"):
            user.email = user_info.get("email")
            user.save()
        if user.name != user_info.get("name"):
            user.name = user_info.get("name", "")
            user.save()
        return user

    def _verify_claims(self):
        """Can check certain attributes"""
        return True

    def create_or_update_user(self):
        if not self._verify_claims():
            return None

        if not self.token.get("userinfo"):
            return None

        user = self.filter_users_by_claims()

        if user and user.is_active:
            return self._update_user(user)
        else:
            return self._create_user()


class OIDCSessionValidator:
    def __init__(self, request):
        """refresh needs to attach the current request"""
        self.request = request

    def _has_access_token_expired(self):
        current_seconds = timezone.now().timestamp()
        token_expiry_seconds = self.request.session.get("oidc_access_token_expiration")
        return token_expiry_seconds and current_seconds > token_expiry_seconds

    def _has_id_token_expired(self):
        current_seconds = timezone.now().timestamp()
        token_expiry_seconds = self.request.session.get("oidc_id_token_expiration")
        return token_expiry_seconds and current_seconds > token_expiry_seconds

    def expired(self):
        """
        Validate the id_token by renewing the id_token by using silence_auth
        TBD : not sure whether it is useful or not, right now the id_token
        will be renewed based on t
        """
        return self._has_access_token_expired() or self._has_id_token_expired()


# POC implementation
def get_aws_access_identity_center_token(token):
    client = boto3.client("sso-oidc")
    try:
        response = client.create_token_with_iam(
            clientId=settings.IDENTITY_CENTRE_OIDC_APPLICATION_ID,  # the application ID (ARN?) from Identity Centre e.g. arn:aws:sso::222222222222:application/ssoins-12345678/apl-87654321
            grantType="urn:ietf:params:oauth:grant-type:jwt-bearer",
            assertion=token["id_token"],  # ID token from EntraID
        )
    except botocore.exceptions.ClientError as ice:
        raise ice
    except Exception as e:
        raise e

    # decode the ID token with pyjwt lib
    aws_token = jwt.decode(jwt=response["idToken"], options={"verify_signature": False})

    sts = boto3.client("sts")
    response = sts.assume_role(
        RoleArn=settings.IAM_BEARER_ROLE_ARN,
        RoleSessionName=f"identity-bearer-{token["userinfo"]["preferred_username"]}",
        ProvidedContexts=[
            {
                "ProviderArn": "arn:aws:iam::aws:contextProvider/IdentityCenter",
                "ContextAssertion": aws_token["sts:identity_context"],
            },
        ],
    )
    # Then use "sts:identity_context" from the token later when calls STS to get temporary credentials
    credentials = {
        "aws_access_key_id": response["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
        "aws_session_token": response["Credentials"]["SessionToken"],
    }
    sts2 = boto3.client("sts", **credentials)
    athena = boto3.client("athena", **credentials, region_name="eu-west-2")
    s3 = boto3.client("s3", **credentials)

    qs_session_name = f"quicksight-test-{token["userinfo"]["preferred_username"]}"

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
        UserName=token["userinfo"]["email"],
        AwsAccountId=settings.COMPUTE_ACCOUNT_ID,
        Namespace="default",
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
    )
    print(url_response)

    # breakpoint()

    # res = athena.start_query_execution(
    #     QueryString='SELECT * FROM "james_lake_form_test_resource_link" limit 10;',
    #     QueryExecutionContext={
    #         'Database': 'julia-lakeformation-database'
    #     },
    #     WorkGroup="primary",
    #     ResultConfiguration={
    #         "OutputLocation": "s3://aws-athena-query-results-eu-west-2-525294151996/",
    #     }
    #     # ResultConfiguration = { 'OutputLocation': 's3://your-bucket/key'}
    # )
    # breakpoint()
