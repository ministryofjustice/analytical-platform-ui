from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

from ap.auth.views.mixins import OIDCLoginRequiredMixin


class IndexView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "home.html"


class HealthcheckView(View):
    def get(self, request):
        return HttpResponse("OK")
