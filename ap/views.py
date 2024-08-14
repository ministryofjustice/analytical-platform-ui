from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "home.html"

    def get_template_names(self) -> list[str]:
        if not self.request.user.is_authenticated:
            self.template_name = "login.html"
        return super().get_template_names()


class HealthcheckView(View):
    def get(self, request):
        return HttpResponse("OK")
