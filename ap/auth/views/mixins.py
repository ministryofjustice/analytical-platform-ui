from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse

from ap.auth.oidc import OIDCSessionValidator


class OIDCLoginRequiredMixin(LoginRequiredMixin):
    """Verify that the current user is (still) authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("login"))
        if OIDCSessionValidator(request).expired():
            request.session["next"] = request.get_full_path()
            return redirect(reverse("login"))
        return super().dispatch(request, *args, **kwargs)
