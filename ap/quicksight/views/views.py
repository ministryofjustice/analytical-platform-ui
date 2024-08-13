from typing import Any

from django.views.generic import TemplateView

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin


class QuicksightView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "quicksight/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["embed_url"] = aws.QuicksightService().get_embed_url(user=self.request.user)
        return context
