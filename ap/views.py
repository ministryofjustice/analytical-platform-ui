from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from ap.auth.oidc import OIDCSessionValidator


class IndexView(TemplateView):
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        """
        If the session has expired, redirect to login
        """
        if OIDCSessionValidator(request).expired():
            return redirect(reverse("login"))
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self) -> list[str]:
        if not self.request.user.is_authenticated:
            self.template_name = "login.html"
        return super().get_template_names()


class HealthcheckView(View):
    def get(self, request):
        return HttpResponse("OK")
