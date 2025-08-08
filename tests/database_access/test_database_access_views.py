# Third-party
import pytest
from django.urls import reverse


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
        "view,user,logged_in,expected_status",
        [
            (database_list, "superuser", True, 200),
            (database_list, "normal_user", True, 200),
            (database_list, "other_user", False, 302),
            (list_tables, "superuser", True, 200),
            (list_tables, "normal_user", True, 200),
            (list_tables, "other_user", False, 302),
            (table_detail, "superuser", True, 200),
            (table_detail, "normal_user", True, 200),
            (table_detail, "other_user", False, 302),
        ],
    )
    def test_access(self, client, users, view, user, logged_in, expected_status):
        if logged_in:
            client.force_login(users[user])
        response = view(client)
        assert response.status_code == expected_status
