from typing import Any

from django.views.generic import TemplateView

from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.aws.quicksight import QuicksightAWSService


class QuicksightView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "quicksight/index.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["embed_url"] = QuicksightAWSService().get_embed_url(user=self.request.user)
        return context
