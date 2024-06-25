from django.views.generic import TemplateView
from controlpanel.auth.views.mixins import OIDCLoginRequiredMixin



class IndexView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "home.html"
