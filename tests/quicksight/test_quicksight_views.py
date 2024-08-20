# Third-party
import pytest
from unittest.mock import patch
from django.urls import reverse


def index(client):
    return client.get(reverse("quicksight:index"))


class TestQuicksightViews():

    @pytest.mark.parametrize(
        "view,user,expected_status",
        [
            (index, "superuser", 200),
            (index, "normal_user", 200),
        ],
    )
    def test_permission(self, client, users, view, user, expected_status):
        client.force_login(users[user])
        response = view(client)
        assert response.status_code == expected_status
