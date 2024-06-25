import pytest
from model_bakery import baker


@pytest.fixture
def superuser(db):
    return baker.make(
        "users.User",
        username="testing_superuser_id",
        is_superuser=True,
        name="alice",
    )


@pytest.fixture
def users(db, superuser):
    return {
        "superuser": superuser,
        "normal_user": baker.make(
            "users.User",
            user_id="testing_normal_user_id",
            username="bob",
            name="bob",
            is_superuser=False,
        ),
        "other_user": baker.make(
            "users.User",
            username="carol",
            name="carol",
            user_id="testing_other_user_id",
        ),
    }
