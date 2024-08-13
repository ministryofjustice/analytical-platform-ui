from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "home.html"


class HealthcheckView(View):
    def get(self, request):
        return HttpResponse("OK")
