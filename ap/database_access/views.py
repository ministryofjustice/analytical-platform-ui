from typing import Any

from django.conf import settings
from django.views.generic import DetailView, TemplateView

import boto3

from ap.auth.views.mixins import OIDCLoginRequiredMixin


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/database/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["databases"] = boto3.client("glue", region_name="eu-west-2").get_databases()[
            "DatabaseList"
        ]
        return context


class DatabaseDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/detail.html"
    context_object_name = "database"

    def get_object(self):
        glue = boto3.client("glue", region_name="eu-west-2")
        response = glue.get_tables(
            CatalogId=settings.GLUE_CATALOG_ID, DatabaseName=self.kwargs["database_name"]
        )
        return {"name": self.kwargs["database_name"], "tables": response["TableList"]}
