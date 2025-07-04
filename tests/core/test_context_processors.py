import pytest
from django.urls import reverse

from ap.core.context_processors import header_context, nav_items


class TestContextProcessors:
    @pytest.fixture
    def request_obj(self, rf, superuser):
        request = rf.get("/")
        request.user = superuser
        return request

    def test_nav_items(self, request_obj):
        expected = [
            {"name": "Home", "url": "/", "active": True},
            {"name": "QuickSight", "url": reverse("quicksight:index"), "active": False},
            {"name": "Database access", "url": reverse("database_access:list"), "active": False},
            {
                "name": "Admin",
                "url": reverse("admin:index"),
                "hide": not request_obj.user.is_staff,
            },
        ]
        assert nav_items(request=request_obj) == {"nav_items": expected}

    def test_header_context(self, request_obj):
        expected_nav_items = [
            {"name": request_obj.user.username, "url": ""},
            {"name": "Sign out", "url": reverse("logout")},
        ]

        context = header_context(request=request_obj)
        assert context.get("header_nav_items") == expected_nav_items
        assert (
            context.get("header_organisation_url")
            == "https://www.gov.uk/government/organisations/ministry-of-justice"
        )
        assert (
            context.get("header_service_url")
            == "https://github.com/ministryofjustice/data-platform"
        )
