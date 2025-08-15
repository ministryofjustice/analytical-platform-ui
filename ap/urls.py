from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("admin/", admin.site.urls),
    path("auth/", include("ap.auth.urls")),
    path("database-access/", include("ap.database_access.urls", namespace="database_access")),
    path("healthcheck/", views.HealthcheckView.as_view(), name="healthcheck"),
    path("quicksight/", include("ap.quicksight.urls", namespace="quicksight")),
]

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
