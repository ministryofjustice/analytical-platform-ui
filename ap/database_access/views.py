from typing import Any

from django.views.generic import TemplateView

import boto3

from ap.auth.views.mixins import OIDCLoginRequiredMixin


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["databases"] = boto3.client("glue", region_name="eu-west-2").get_databases()[
            "DatabaseList"
        ]

        return context
