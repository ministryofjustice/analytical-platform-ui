from django.urls import reverse


def nav_items(request):
    if not request.user.is_authenticated:
        return {}
    quicksight_url = reverse("quicksight")
    datasources_url = reverse("datasources-list")
    return {
        "nav_items": [
            {"name": "Home", "url": "/", "active": request.get_full_path() == "/"},
            {
                "name": "Quicksight",
                "url": quicksight_url,
                "active": request.get_full_path() == quicksight_url,
            },
            {
                "name": "Datasources",
                "url": datasources_url,
                "active": datasources_url in request.get_full_path(),
            },
        ]
    }


def header_context(request):
    is_logged_in = request.user and request.user.is_authenticated
    return {
        "header_nav_items": [
            {
                "name": request.user.name if is_logged_in else "",
                "url": "",
            },
            {
                "name": "Sign out" if is_logged_in else "Sign in",
                "url": reverse("logout") if is_logged_in else reverse("login"),
            },
        ],
        "header_organisation_url": "https://www.gov.uk/government/organisations/ministry-of-justice",  # noqa
        "header_service_url": "https://github.com/ministryofjustice/data-platform",
    }
