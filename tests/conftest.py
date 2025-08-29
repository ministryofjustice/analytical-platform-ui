import pytest
from model_bakery import baker

from tests.fixtures.aws_fixtures import *  # noqa


@pytest.fixture
def superuser(db):
    return baker.make(
        "users.User",
        is_superuser=True,
        email="superuser@example.com",
    )


@pytest.fixture
def users(db, superuser):
    return {
        "superuser": superuser,
        "normal_user": baker.make(
            "users.User",
            email="normal_user@example.com",
            is_superuser=False,
        ),
        "other_user": baker.make(
            "users.User",
            email="carol@example.com",
            is_superuser=False,
        ),
    }
