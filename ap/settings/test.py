# First-party/Local
from ap.settings.common import *  # noqa: F403

ENV = "test"

LOG_LEVEL = "WARNING"

LOGGING["loggers"]["django_structlog"]["level"] = LOG_LEVEL  # noqa: F405
LOGGING["loggers"]["ap"]["level"] = LOG_LEVEL  # noqa: F405

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

AZURE_CLIENT_ID = "testing"
AZURE_CODE_CHALLENGE_METHOD = "testing"
AZURE_RP_SCOPES = "openid email profile offline_access"
AZURE_OP_CONF_URL = "https://testing.oidc.com/.well-known/openid-configuration"


AUTHLIB_OAUTH_CLIENTS = {
    "azure": {
        "client_id": AZURE_CLIENT_ID,
        "server_metadata_url": AZURE_OP_CONF_URL,
        "client_kwargs": {
            "scope": AZURE_RP_SCOPES,
            "response_type": "code",
            "token_endpoint_auth_method": "none",
            "code_challenge_method": AZURE_CODE_CHALLENGE_METHOD,
        },
    },
}

GLUE_CATALOG_ID = "123456789012"
DEFAULT_STS_ROLE_TO_ASSUME = "arn:aws:iam::123456789012:role/test-role-12345"

PRODUCER_ACCOUNT_ID = "123456789012"
