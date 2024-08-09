from typing import Any

from django.conf import settings
from django.views.generic import DetailView, TemplateView

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.database_access.models.access import TableAccess


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/database/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["databases"] = aws.GlueService().client.get_databases()["DatabaseList"]
        return context


class DatabaseDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/detail.html"
    context_object_name = "database"

    def get_object(self):
        response = aws.GlueService().client.get_tables(
            CatalogId=settings.GLUE_CATALOG_ID, DatabaseName=self.kwargs["database_name"]
        )
        return {"name": self.kwargs["database_name"], "tables": response["TableList"]}


class TableDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/table.html"
    context_object_name = "table"

    def get_object(self):
        response = aws.GlueService().client.get_table(
            CatalogId=settings.GLUE_CATALOG_ID,
            DatabaseName=self.kwargs["database_name"],
            Name=self.kwargs["table_name"],
        )
        return {
            "name": self.kwargs["table_name"],
            "is_registered_with_lake_formation": response["Table"]["IsRegisteredWithLakeFormation"],
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["access_queryset"] = TableAccess.objects.filter(
            database_access__user=self.request.user,
            database_access__database_name=self.kwargs["database_name"],
            table_name=self.kwargs["table_name"],
        ).select_related("database_access")
        return context
