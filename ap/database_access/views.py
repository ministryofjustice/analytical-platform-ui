from typing import Any

import botocore
import sentry_sdk
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin

from ap import aws
from ap.auth.views.mixins import OIDCLoginRequiredMixin
from ap.database_access import forms

from . import models


class FilterAccessMixin(ContextMixin):
    context_list_name = "objects"

    def get_user_access_objects(self):
        raise NotImplementedError()

    def get_all_objects(self):
        raise NotImplementedError()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        filter_by = self.request.GET.get("filter", {})
        match filter_by:
            case "my-access":
                context[self.context_list_name] = self.get_user_access_objects()
            case "all":
                context[self.context_list_name] = self.get_all_objects()
            case _:
                context[self.context_list_name] = self.get_all_objects()

        return context


class BreadcrumbsMixin(ContextMixin):
    def get_breadcrumbs(self):
        raise NotImplementedError()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.get_breadcrumbs()
        return context


class DatabaseListView(OIDCLoginRequiredMixin, FilterAccessMixin, TemplateView):
    template_name = "database_access/database/list.html"
    context_list_name = "databases"

    def get_all_objects(self):
        return aws.GlueService().get_database_list()

    def get_user_access_objects(self):
        return models.DatabaseAccess.objects.filter(user=self.request.user)


class DatabaseDetailView(OIDCLoginRequiredMixin, FilterAccessMixin, BreadcrumbsMixin, TemplateView):
    template_name = "database_access/database/detail.html"
    context_list_name = "tables"

    def get_breadcrumbs(self):
        return [
            {"text": "Databases", "url": reverse("database_access:list")},
        ]

    def get_database(self):
        database = aws.GlueService().get_database_detail(database_name=self.kwargs["database_name"])
        if not database:
            raise Http404("Database not found")
        return database

    def get_all_objects(self):
        tables = aws.GlueService().get_table_list(database_name=self.kwargs["database_name"])
        if not tables:
            raise Http404("Database not found")
        return tables

    def get_user_access_objects(self):
        database = aws.GlueService().get_database_detail(database_name=self.kwargs["database_name"])
        if not database:
            raise Http404("Database not found")
        return models.TableAccess.objects.filter(
            database_access__name=self.kwargs["database_name"],
            database_access__user=self.request.user,
        )


class TableDetailView(OIDCLoginRequiredMixin, BreadcrumbsMixin, DetailView):
    template_name = "database_access/database/table.html"
    context_object_name = "table"

    def get_breadcrumbs(self):
        return [
            {"text": "Databases", "url": reverse("database_access:list")},
            {
                "text": self.kwargs["database_name"],
                "url": reverse(
                    "database_access:detail",
                    kwargs={"database_name": self.kwargs["database_name"]},
                ),
            },
        ]

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
            .prefetch_related("grantable_permissions")
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
        except models.TableAccess.DoesNotExist as e:
            raise Http404() from e

        return table_access.grantable_permissions.all()

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        try:
            return super().form_valid(form)
        except botocore.exceptions.ClientError as error:
            sentry_sdk.capture_exception(error)
            form.add_error(None, "An error occured granting permissions")
            return self.form_invalid(form)

    def get_success_url(self) -> str:
        return reverse(
            "database_access:table_detail",
            kwargs={
                "database_name": self.kwargs["database_name"],
                "table_name": self.kwargs["table_name"],
            },
        )


class GrantTableAccessView(OIDCLoginRequiredMixin, TableAccessMixin, BreadcrumbsMixin, CreateView):
    template_name = "database_access/database/grant_access.html"
    form_class = forms.AccessForm

    def get_breadcrumbs(self):
        return [
            {"text": "Databases", "url": reverse("database_access:list")},
            {
                "text": self.kwargs["database_name"],
                "url": reverse(
                    "database_access:detail",
                    kwargs={"database_name": self.kwargs["database_name"]},
                ),
            },
            {
                "text": self.kwargs["table_name"],
                "url": reverse(
                    "database_access:table_detail",
                    kwargs={
                        "database_name": self.kwargs["database_name"],
                        "table_name": self.kwargs["table_name"],
                    },
                ),
            },
        ]

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


class ManageTableAccessView(OIDCLoginRequiredMixin, TableAccessMixin, BreadcrumbsMixin, UpdateView):
    template_name = "database_access/database/manage_access.html"
    model = models.TableAccess
    form_class = forms.ManageAccessForm
    context_object_name = "access"

    def get_breadcrumbs(self):
        return [
            {"text": "Databases", "url": reverse("database_access:list")},
            {
                "text": self.kwargs["database_name"],
                "url": reverse(
                    "database_access:detail",
                    kwargs={"database_name": self.kwargs["database_name"]},
                ),
            },
            {
                "text": self.kwargs["table_name"],
                "url": reverse(
                    "database_access:table_detail",
                    kwargs={
                        "database_name": self.kwargs["database_name"],
                        "table_name": self.kwargs["table_name"],
                    },
                ),
            },
        ]

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


class RevokeTableAccessView(OIDCLoginRequiredMixin, BreadcrumbsMixin, DeleteView):
    template_name = "database_access/database/revoke_access.html"
    model = models.TableAccess
    context_object_name = "access"

    def get_breadcrumbs(self):
        return [
            {"text": "Databases", "url": reverse("database_access:list")},
            {
                "text": self.kwargs["database_name"],
                "url": reverse(
                    "database_access:detail",
                    kwargs={"database_name": self.kwargs["database_name"]},
                ),
            },
            {
                "text": self.kwargs["table_name"],
                "url": reverse(
                    "database_access:table_detail",
                    kwargs={
                        "database_name": self.kwargs["database_name"],
                        "table_name": self.kwargs["table_name"],
                    },
                ),
            },
        ]

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related("database_access__user")

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
            sentry_sdk.capture_exception(error)
            form.add_error(
                None,
                "An error occured revoking permissions. Please try again. If the issue persists, contact the AP support.",  # noqa
            )
            return self.form_invalid(form)
