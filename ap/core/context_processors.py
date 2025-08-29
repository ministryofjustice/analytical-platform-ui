from django.urls import reverse


def nav_items(request):
    if not request.user.is_authenticated:
        return {"nav_items": []}

    return {
        "nav_items": [
            {"name": "Home", "url": "/", "active": request.get_full_path() == "/"},
            {
                "name": "Admin",
                "url": reverse("admin:index"),
                "hide": not request.user.is_staff,
            },
        ]
    }


def header_context(request):
    is_logged_in = request.user.is_authenticated
    return {
        "header_nav_items": [
            {
                "name": "Sign out" if is_logged_in else "Sign in",
                "url": reverse("logout") if is_logged_in else reverse("login"),
            },
        ],
        "header_organisation_url": "https://www.gov.uk/government/organisations/ministry-of-justice",  # noqa
        "header_service_url": "https://github.com/ministryofjustice/data-platform",
    }
