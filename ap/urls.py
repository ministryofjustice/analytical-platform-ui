from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("auth/", include("ap.auth.urls")),
    path("admin/", admin.site.urls),
    path("databases/", include("ap.databases.urls", namespace="databases")),
]
