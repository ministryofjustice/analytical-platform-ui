from django.urls import include, path

from controlpanel.interfaces.web.views import IndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("auth/", include("controlpanel.auth.urls")),
]
