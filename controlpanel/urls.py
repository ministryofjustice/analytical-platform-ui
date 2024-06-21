from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("controlpanel.core.urls")),
    path("auth/", include("controlpanel.auth.urls")),
    path("admin/", admin.site.urls),
]
