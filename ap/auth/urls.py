from django.urls import path

from . import views

urlpatterns = [
    path("authenticate/", views.OIDCAuthenticationView.as_view(), name="authenticate"),
    path("login/", views.OIDCLoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("login-fail/", views.LoginFail.as_view(), name="login-fail"),
]
