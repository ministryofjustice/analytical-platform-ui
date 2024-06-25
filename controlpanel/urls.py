from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("auth/", include("controlpanel.auth.urls")),
    path("admin/", admin.site.urls),
]
