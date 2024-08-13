from typing import Any

from django.views.generic import DetailView, TemplateView

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/database/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["databases"] = aws.GlueService().get_database_list()
        return context


class DatabaseDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/detail.html"
    context_object_name = "database"

    def get_object(self):
        tables = aws.GlueService().get_table_list(database_name=self.kwargs["database_name"])
        return {"name": self.kwargs["database_name"], "tables": tables}


class TableDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/table.html"
    context_object_name = "table"

    def get_object(self):
        table = aws.GlueService().get_table_detail(
            database_name=self.kwargs["database_name"], table_name=self.kwargs["table_name"]
        )
        return {
            "name": self.kwargs["table_name"],
            "is_registered_with_lake_formation": table.get("IsRegisteredWithLakeFormation"),
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context
