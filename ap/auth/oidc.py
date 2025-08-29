import boto3
import botocore
import botocore.exceptions
import jwt
import structlog
from authlib.integrations.django_client import OAuth
from django.conf import settings
from django.utils import timezone

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
        oid = self.token.get("userinfo", {}).get("oid")
        user = User.objects.filter(entra_oid=oid).first()
        return user

    def _create_user(self):
        user_info = self.token.get("userinfo")
        return User.objects.create(
            email=user_info.get("email"),
            entra_oid=user_info.get("oid"),
        )

    def _update_user(self, user):
        user_info = self.token.get("userinfo")
        # Update the non-key information to sync the user's info
        # with user profile from idp when the user's username is not changed.

        if user.email != user_info.get("email"):
            user.email = user_info.get("email")
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
def get_aws_identity_center_access_token(id_token):
    """
    Requires ID token for a user from EntraID
    """
    client = boto3.client("sso-oidc")
    try:
        response = client.create_token_with_iam(
            clientId=settings.IDENTITY_CENTRE_OIDC_ARN,
            grantType="urn:ietf:params:oauth:grant-type:jwt-bearer",
            assertion=id_token,
        )
    except botocore.exceptions.ClientError as ice:
        raise ice
    except Exception as e:
        raise e

    # decode the ID token with pyjwt lib
    aws_token = jwt.decode(jwt=response["idToken"], options={"verify_signature": False})
    return aws_token


def get_aws_credentials(aws_token):
    """
    Gets AWS credentials passing the identity context of the user from the AWS access token
    """
    sts = boto3.client("sts")
    response = sts.assume_role(
        RoleArn=settings.IAM_BEARER_ROLE_ARN,
        RoleSessionName=f"identity-bearer-{aws_token['sub']}",
        ProvidedContexts=[
            {
                "ProviderArn": "arn:aws:iam::aws:contextProvider/IdentityCenter",
                "ContextAssertion": aws_token["sts:identity_context"],
            },
        ],
    )
    credentials = {
        "aws_access_key_id": response["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
        "aws_session_token": response["Credentials"]["SessionToken"],
    }
    return credentials
