from typing import Any

from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

import botocore

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.database_access import forms

from . import models


class DatabaseListView(OIDCLoginRequiredMixin, TemplateView):
    template_name = "database_access/database/list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if "my-databases" in self.request.GET.get("sort", {}):
            context["databases"] = models.DatabaseAccess.objects.filter(user=self.request.user)
        else:
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
        context["access_queryset"] = (
            models.TableAccess.objects.select_related("database_access__user")
            .filter(
                database_access__name=self.kwargs["database_name"], name=self.kwargs["table_name"]
            )
            .order_by("database_access__user__email")
        )
        context["access_url"] = reverse(
            "database_access:grant_table_access",
            kwargs={
                "database_name": self.kwargs["database_name"],
                "table_name": self.kwargs["table_name"],
            },
        )
        context["can_manage_access"] = self.request.user.can_manage_access(
            database_name=self.kwargs["database_name"],
            table_name=self.kwargs["table_name"],
        )
        return context


class TableAccessMixin(SingleObjectMixin):
    def get_grantable_access(self):
        if self.request.user.is_superuser:
            return models.Permission.objects.filter(entity=models.Permission.Entity.TABLE)

        try:
            table_access = models.TableAccess.objects.get(
                name=self.kwargs["table_name"],
                database_access__name=self.kwargs["database_name"],
                database_access__user=self.request.user,
                grantable_permissions__isnull=False,
            )
        except models.TableAccess.DoesNotExist:
            raise Http404()

        return table_access.grantable_permissions.all()

    def get_success_url(self) -> str:
        return reverse(
            "database_access:table_detail",
            kwargs={
                "database_name": self.kwargs["database_name"],
                "table_name": self.kwargs["table_name"],
            },
        )

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        try:
            return super().form_valid(form)
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "InvalidInputException":
                form.add_error(None, str(error))
                return self.form_invalid(form)
            raise error


class GrantTableAccessView(OIDCLoginRequiredMixin, TableAccessMixin, CreateView):
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["table"] = self.get_object()
        return context


class ManageTableAccessView(OIDCLoginRequiredMixin, TableAccessMixin, UpdateView):
    template_name = "database_access/database/manage_access.html"
    model = models.TableAccess
    form_class = forms.ManageAccessForm
    context_object_name = "access"

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related("database_access__user")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs.update(
            {
                "grantable_access": self.get_grantable_access(),
            }
        )
        return form_kwargs


class RevokeTableAccessView(OIDCLoginRequiredMixin, TableAccessMixin, DeleteView):
    template_name = "database_access/database/revoke_access.html"
    model = models.TableAccess
    context_object_name = "access"

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related("database_access__user")
