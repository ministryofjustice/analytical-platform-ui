from typing import Any

from django.conf import settings
from django.views.generic import DetailView, TemplateView

import boto3

from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.database_access.models.access import TableAccess


def glue_client():
    sts = boto3.client("sts")
    response = sts.assume_role(
        RoleArn=settings.DEFAULT_ROLE_ARN,
        RoleSessionName="analytical-platform-ui-quicksight-session",
    )
    return boto3.client(
        "glue",
        **{
            "aws_access_key_id": response["Credentials"]["AccessKeyId"],
            "aws_secret_access_key": response["Credentials"]["SecretAccessKey"],
            "aws_session_token": response["Credentials"]["SessionToken"],
        },
        region_name="eu-west-2",
    )


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/database/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["databases"] = glue_client().get_databases()["DatabaseList"]
        return context


class DatabaseDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/detail.html"
    context_object_name = "database"

    def get_object(self):
        response = glue_client().get_tables(
            CatalogId=settings.GLUE_CATALOG_ID, DatabaseName=self.kwargs["database_name"]
        )
        return {"name": self.kwargs["database_name"], "tables": response["TableList"]}


class TableDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/table.html"
    context_object_name = "table"

    def get_object(self):
        response = glue_client().get_table(
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
