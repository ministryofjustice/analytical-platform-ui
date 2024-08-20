# Third-party
from django.urls import reverse

import pytest


def database_list(client):
    return client.get(reverse("database_access:list"))


def list_tables(client):
    kwargs = {"database_name": "test_database"}
    return client.get(reverse("database_access:detail", kwargs=kwargs))


def table_detail(client):
    kwargs = {"database_name": "test_database", "table_name": "test_table_1"}
    return client.get(reverse("database_access:table_detail", kwargs=kwargs))


class TestDatabaseAccessViews:

    @pytest.mark.parametrize(
        "view,user,expected_status",
        [
            (database_list, "superuser", 200),
            (database_list, "normal_user", 200),
            (list_tables, "superuser", 200),
            (list_tables, "normal_user", 200),
            (table_detail, "superuser", 200),
            (table_detail, "normal_user", 200),
        ],
    )
    def test_permission(self, client, users, view, user, expected_status):
        client.force_login(users[user])
        response = view(client)
        assert response.status_code == expected_status
