from .common import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [".localhost", "127.0.0.1"]

QUICKSIGHT_DOMAINS = ["http://localhost:8000"]

ENV = "local"

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]
