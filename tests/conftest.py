import pytest
from model_bakery import baker

from tests.fixtures.aws_fixtures import *  # noqa


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


@pytest.fixture
def permissions(db):
    return {
        "select_table": baker.make(
            "database_access.Permission",
            name="select",
            entity="table",
            display_name="Select",
        ),
        "select_db": baker.make(
            "database_access.Permission",
            name="select",
            entity="database",
            display_name="Select",
        ),
        "describe": baker.make(
            "database_access.Permission",
            name="describe",
            entity="database",
            display_name="Describe",
        ),
    }


@pytest.fixture
def database_access(db, users, permissions):
    return {
        "test_db_1": baker.make(
            "database_access.DatabaseAccess",
            user=users["normal_user"],
            name="test_db_1",
            permissions=[permissions["describe"]],
            grantable_permissions=[permissions["describe"]],
        ),
        "test_db_2": baker.make(
            "database_access.DatabaseAccess",
            user=users["other_user"],
            name="test_db_2",
            permissions=[permissions["describe"]],
            grantable_permissions=[permissions["describe"]],
        ),
    }


@pytest.fixture
def table_access(db, database_access, permissions):
    return {
        "table_1": baker.make(
            "database_access.TableAccess",
            database_access=database_access["test_db_1"],
            name="table_1",
            permissions=[permissions["select_table"]],
            grantable_permissions=[permissions["select_table"]],
        ),
        "table_2": baker.make(
            "database_access.TableAccess",
            database_access=database_access["test_db_1"],
            name="table_2",
            permissions=[permissions["select_table"]],
            grantable_permissions=[],
        ),
        "table_1_db_2": baker.make(
            "database_access.TableAccess",
            database_access=database_access["test_db_2"],
            name="table_1",
            permissions=[permissions["select_table"]],
            grantable_permissions=[permissions["select_table"]],
        ),
    }
