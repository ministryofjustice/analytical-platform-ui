import time

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

import sentry_sdk
from authlib.common.security import generate_token
from authlib.integrations.django_client import OAuthError

from ap.auth.oidc import OIDCSubAuthenticationBackend, oauth
from ap.auth.utils import pkce_transform


class OIDCLoginView(View):
    def get(self, request):
        code_verifier = generate_token(64)
        code_challenge = pkce_transform(code_verifier)

        redirect_uri = request.build_absolute_uri(reverse("authenticate"))

        return oauth.azure.authorize_redirect(request, redirect_uri, code_challenge=code_challenge)


class OIDCAuthenticationView(View):
    def _update_sessions(self, request, token):
        """TBD should we consider renewing the id_token?"""
        request.session["oidc_id_token_renew_gap"] = (
            time.time() + settings.AZURE_RENEW_ID_TOKEN_EXPIRY_SECONDS
        )
        request.session["oidc_access_token_expiration"] = token.get("expires_at")
        request.session["oidc_id_token_expiration"] = token["userinfo"].get("exp")

        if token.get("refresh_token"):
            request.session["refresh_token"] = token["refresh_token"]

    def _login_success(self, request, user, token):
        auth.login(self.request, user)
        self._update_sessions(request, token)

    @property
    def failure_url(self):
        return reverse("login-fail")

    def _login_failure(self):
        return redirect(self.failure_url)

    def get(self, request):
        try:
            token = oauth.azure.authorize_access_token(request)
            request.session["entra_access_token"] = token
            oidc_auth = OIDCSubAuthenticationBackend(token)
            user = oidc_auth.create_or_update_user()
            if not user:
                return self._login_failure()
            else:
                self._login_success(request, user, token)
                return redirect("/")
        except OAuthError as error:
            sentry_sdk.capture_exception(error)
            return self._login_failure()


class OIDCLogoutView(View):
    http_method_names = ["get", "post"]

    def post(self, request):
        logout_url = settings.AZURE_LOGOUT_URL

        if request.user.is_authenticated:
            auth.logout(request)

        return redirect(logout_url)

    def get(self, request):
        if self.get_settings("ALLOW_LOGOUT_GET_METHOD", False):
            return self.post(request)
        return HttpResponseNotAllowed(["POST"])


class LogoutView(OIDCLogoutView):
    def get(self, request):
        return super().post(request)


class LoginFail(TemplateView):
    template_name = "login-fail.html"

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("/")
        return super().get(request, *args, **kwargs)
