"""
Django settings for controlpanel project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from os.path import abspath, dirname, join
from pathlib import Path

import structlog

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Name of the project
PROJECT_NAME = "controlpanel"

# Absolute path of project Django directory
DJANGO_ROOT = dirname(dirname(abspath(__file__)))

# Absolute path of project directory
PROJECT_ROOT = dirname(DJANGO_ROOT)

# Name of the deployment environment (dev/prod)
ENV = os.environ.get("ENV", "dev")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = os.environ.get("SECRET_KEY", "please_change_me")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Application definition

INSTALLED_APPS = [
    # Django admin
    "django.contrib.admin",
    # Django built-in auth models
    "django.contrib.auth",
    # Django models
    "django.contrib.contenttypes",
    # Django sessions
    "django.contrib.sessions",
    # Django flash messages
    "django.contrib.messages",
    # Django collect static files into a single location
    "django.contrib.staticfiles",
    # Provides shell_plus, runserver_plus, etc
    "django_extensions",
    # frontend component integration with govuk_frontend node-js package
    "govuk_frontend_django",
    # Provide structured log service
    "django_structlog",
    # The core logic of Control panel
    "controlpanel.core",
    # The frontend part of Control panel
    "controlpanel.interfaces.web",
]

MIDDLEWARE = [
    "controlpanel.middleware.DisableClientSideCachingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Structured logging
    "django_structlog.middlewares.RequestMiddleware",
]

# The list of authentication backend used for checking user's access to app
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

ROOT_URLCONF = "controlpanel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [join(DJANGO_ROOT, "interfaces", "web", "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": f"{PROJECT_NAME}.interfaces.web.jinja2.environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = f"{PROJECT_NAME}.wsgi.application"

ASGI_APPLICATION = f"{PROJECT_NAME}.routing.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# -- Database
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
ENABLE_DB_SSL = (
    str(os.environ.get("ENABLE_DB_SSL", DB_HOST not in ["127.0.0.1", "localhost"])).lower()
    == "true"
)
DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", PROJECT_NAME),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": DB_HOST,
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

if ENABLE_DB_SSL:
    DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Directory to collect static files into
# STATIC_ROOT = join(PROJECT_ROOT, "static")
STATIC_ROOT = join(PROJECT_ROOT, "run", "static")

# Django looks in these locations for additional static assets to collect
STATICFILES_DIRS = [
    join(PROJECT_ROOT, "static"),
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -- Auth URL

LOGIN_URL = "login"

LOGOUT_REDIRECT_URL = "/"

ALLOWED_HOSTS: list = []

# Whitelist values for the HTTP Host header, to prevent certain attacks
ALLOWED_HOSTS = [host for host in os.environ.get("ALLOWED_HOSTS", "").split() if host]

# -- HTTP headers
# Sets the X-Content-Type-Options: nosniff header
SECURE_CONTENT_TYPE_NOSNIFF = True

# Secure the CSRF cookie
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Secure the session cookie
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

# Custom user model class
AUTH_USER_MODEL = "core.User"

# -- OIDC Settings
OIDC_DOMAIN = os.environ.get("OIDC_DOMAIN")
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
OIDC_RP_SCOPES = "openid email profile offline_access"
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = os.environ.get("OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS", 60 * 60)
OIDC_LOGOUT_URL = f"https://{OIDC_DOMAIN}/v2/logout"

AUTHLIB_OAUTH_CLIENTS = {
    "auth0": {
        "client_id": OIDC_RP_CLIENT_ID,
        "client_secret": OIDC_RP_CLIENT_SECRET,
        "server_metadata_url": os.environ.get("OIDC_OP_CONF_URL"),
        "client_kwargs": {"scope": OIDC_RP_SCOPES},
    }
}


# -- Logging Settings : structLog

LOG_LEVEL = os.environ.get("LOG_LEVEL", "debug").upper()
DEFAULT_LOG_FORMATTER = os.environ.get("DEFAULT_LOG_FORMATTER", "plain_console")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": DEFAULT_LOG_FORMATTER,
        },
    },
    "loggers": {
        "django_structlog": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
        "root": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
