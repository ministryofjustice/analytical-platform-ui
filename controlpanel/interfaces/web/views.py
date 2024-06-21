from typing import Any

from django.views.generic import TemplateView

from controlpanel.auth.views.mixins import OIDCLoginRequiredMixin
from controlpanel.core.models import User


class IndexView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "users": User.objects.all(),
            }
        )
        return context
