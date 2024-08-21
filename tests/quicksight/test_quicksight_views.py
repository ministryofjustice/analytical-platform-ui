# Third-party
from django.urls import reverse

import pytest


def index(client):
    return client.get(reverse("quicksight:index"))


class TestQuicksightViews:

    @pytest.mark.parametrize(
        "view,user,logged_in,expected_status",
        [
            (index, "superuser", True, 200),
            (index, "normal_user", True, 200),
            (index, "other_user", False, 302),
        ],
    )
    def test_access(self, client, users, view, user, logged_in, expected_status):
        if logged_in:
            client.force_login(users[user])
        response = view(client)
        assert response.status_code == expected_status
