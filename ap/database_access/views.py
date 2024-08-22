from typing import Any

from django.http import Http404, HttpResponseForbidden
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.database_access import forms

from . import models


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
        if not tables:
            raise Http404("Database not found")
        return {"name": self.kwargs["database_name"], "tables": tables}


class TableDetailView(OIDCLoginRequiredMixin, DetailView):
    template_name = "database_access/database/table.html"
    context_object_name = "table"

    def get_object(self):
        table = aws.GlueService().get_table_detail(
            database_name=self.kwargs["database_name"], table_name=self.kwargs["table_name"]
        )
        if not table:
            raise Http404("Table not found")
        return {
            "name": self.kwargs["table_name"],
            "is_registered_with_lake_formation": table.get("IsRegisteredWithLakeFormation"),
        }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["access_queryset"] = models.TableAccess.objects.select_related(
            "database_access__user"
        )
        context["access_url"] = reverse(
            "database_access:grant_table_access",
            kwargs={
                "database_name": self.kwargs["database_name"],
                "table_name": self.kwargs["table_name"],
            },
        )
        return context


class GrantTableAccessView(OIDCLoginRequiredMixin, CreateView):
    template_name = "database_access/database/grant_access.html"
    form_class = forms.AccessForm

    def get_object(self):
        table = aws.GlueService().get_table_detail(
            database_name=self.kwargs["database_name"], table_name=self.kwargs["table_name"]
        )
        if not table:
            raise Http404("Table not found")

        return {
            "name": self.kwargs["table_name"],
            "database_name": self.kwargs["database_name"],
        }

    def get_grantable_access(self) -> Any:
        if self.request.user.is_superuser:
            return models.AccessLevel.objects.filter(entity=models.AccessLevel.Entity.TABLE)

        user_access = (
            models.TableAccess.objects.filter(
                name=self.kwargs["table_name"],
                database_access__name=self.kwargs["database_name"],
                database_access__user=self.request.user,
                access_levels__grantable=True,
            )
            .prefetch_related("access_levels")
            .first()
        )

        if not user_access:
            raise HttpResponseForbidden("User does not have grantable access to any tables")

        return user_access.access_levels.all()

    def get_form_kwargs(self) -> dict[str, Any]:
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            {
                "table_name": self.kwargs["table_name"],
                "database_name": self.kwargs["database_name"],
                "grantable_access": self.get_grantable_access(),
            }
        )
        return form_kwargs

    def get_initial(self) -> dict[str, Any]:
        data = super().get_initial()
        data["name"] = self.kwargs["table_name"]
        data["database_name"] = self.kwargs["database_name"]
        return data

    def get_success_url(self) -> str:
        return reverse(
            "database_access:table_detail",
            kwargs={
                "database_name": self.kwargs["database_name"],
                "table_name": self.kwargs["table_name"],
            },
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["table"] = self.get_object()
        return context
