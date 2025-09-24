from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView

from ap import aws

from .models import SharedResource
from .utils import (
    create_or_update_shared_resources,
    transform_database,
    transform_database_list,
    transform_table,
    transform_table_list,
)


class SharedResourceListView(ListView):
    template_name = "poc/shared_resources.html"
    model = SharedResource
    context_object_name = "ram_shares"


# class RAMShareResourcesView(DetailView):
#     template_name = "poc/ram_share_resources.html"
#     model = RAMShare
#     context_object_name = "ram_share"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["resources"] = list(self.object.get_shared_resources())
#         return context


class RefreshSharedResourceView(View):
    def post(self, request, *args, **kwargs):
        try:
            create_or_update_shared_resources()
            messages.success(request, "Shared Resources have been successfully refreshed.")
        except Exception as e:
            messages.error(request, f"Failed to refresh Shared Resources: {str(e)}")

        return HttpResponseRedirect(reverse("poc:index"))


class DeleteSharedResourceView(View):
    def post(self, request, *args, **kwargs):
        for obj in SharedResource.objects.all():
            obj.delete()
        messages.success(request, "Shared Resources have been successfully deleted.")
        return HttpResponseRedirect(reverse("poc:index"))


class DatabaseListView(TemplateView):
    template_name = "poc/database_list.html"

    def get_context_data(self, **kwargs):
        glue = aws.GlueService()
        databases = transform_database_list(glue.get_database_list())

        context = super().get_context_data(**kwargs)
        context["databases"] = databases
        return context


class DatabaseDetailView(TemplateView):
    template_name = "poc/database_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        database_rl_name = kwargs.get("database_rl_name")
        glue = aws.GlueService()
        database = transform_database(glue.get_database_detail(database_rl_name))

        if database:
            tables = transform_table_list(
                glue.get_table_list(database["name"], database["catalog_id"])
            )

            context["tables"] = tables

            resource = {
                "Database": {
                    "CatalogId": database["rl_catalog_id"],
                    "Name": database_rl_name,
                },
            }
            lake_formation = aws.LakeFormationService()
            database_permissions = lake_formation.list_object_permissions(
                resource_type="DATABASE", resource=resource
            )

            context["database_permissions"] = database_permissions

        context["database"] = database

        return context


class GrantDatabasePermissionsView(View):
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get("user")
            database_rl_name = kwargs.get("database_rl_name")
            resource_catalog_id = str(kwargs.get("resource_catalog_id"))

            iam = aws.IAMService()
            role = iam.get_role(role_name=f"{username}")
            principal = role.get("Arn")

            lake_formation = aws.LakeFormationService()
            # Grants describe permission on
            lake_formation.grant_database_permissions(
                database=database_rl_name,
                principal=principal,
            )
            messages.success(request, "Permissions granted.")
        except Exception as e:
            messages.error(request, f"Failed to grant permissions: {str(e)}")

        return HttpResponseRedirect(
            reverse("poc:database_detail", args=[resource_catalog_id, database_rl_name])
        )


class RevokeDatabasePermissionsView(View):
    def post(self, request, *args, **kwargs):
        try:
            principal = request.POST.get("principal")
            database_permissions = request.POST.get("permissions").split(", ")
            resource_catalog_id = str(kwargs.get("resource_catalog_id"))
            database_rl_name = kwargs.get("database_rl_name")
            lake_formation = aws.LakeFormationService()

            lake_formation.revoke_database_permissions(
                database=database_rl_name,
                principal=principal,
                permissions=database_permissions,
            )

            messages.success(request, "Permissions Revoked.")
        except Exception as e:
            messages.error(request, f"Failed to revoke permissions: {str(e)}")

        return HttpResponseRedirect(
            reverse("poc:database_detail", args=[resource_catalog_id, database_rl_name])
        )


class TableDetailView(TemplateView):
    template_name = "poc/table_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource_catalog_id = str(kwargs.get("resource_catalog_id"))
        database_rl_name = kwargs.get("database_rl_name")
        table_name = kwargs.get("table_name")
        glue = aws.GlueService()
        database = transform_database(glue.get_database_detail(database_rl_name))
        database_name = database["name"]
        table = transform_table(
            glue.get_table_detail(database_name, table_name, resource_catalog_id)
        )

        if table:
            resource = {
                "Table": {
                    "CatalogId": resource_catalog_id,
                    "DatabaseName": database_name,
                    "Name": table["name"],
                },
            }
            lake_formation = aws.LakeFormationService()
            table_permissions = lake_formation.list_object_permissions(
                resource_type="TABLE", resource=resource
            )

            context["table_permissions"] = table_permissions

        context["database"] = database
        context["table"] = table
        return context


class GrantTablePermissionsView(View):
    def post(self, request, *args, **kwargs):
        try:
            username = request.POST.get("user")
            resource_catalog_id = str(kwargs.get("resource_catalog_id"))
            database_rl_name = kwargs.get("database_rl_name")
            table_name = kwargs.get("table_name")

            iam = aws.IAMService()
            role = iam.get_role(role_name=f"{username}")
            principal = role.get("Arn")

            table_permissions = ["SELECT", "DESCRIBE"]
            glue = aws.GlueService()
            database = transform_database(glue.get_database_detail(database_rl_name))
            database_name = database["name"]
            lake_formation = aws.LakeFormationService()

            # Grants describe permission on
            lake_formation.grant_database_permissions(
                database=database_rl_name,
                principal=principal,
            )

            table = transform_table(
                glue.get_table_detail(database_name, table_name, resource_catalog_id)
            )

            lake_formation.grant_table_permissions(
                database=database_name,
                table=table["name"],
                resource_catalog_id=table["catalog_id"],
                principal=principal,
                permissions=table_permissions,
            )
            messages.success(request, "Permissions granted.")
        except Exception as e:
            messages.error(request, f"Failed to grant permissions: {str(e)}")

        return HttpResponseRedirect(
            reverse("poc:table_detail", args=[resource_catalog_id, database_rl_name, table_name])
        )


class RevokeTablePermissionsView(View):
    def post(self, request, *args, **kwargs):
        try:
            principal = request.POST.get("principal")
            permissions = request.POST.get("permissions").split(", ")
            resource_catalog_id = str(kwargs.get("resource_catalog_id"))
            database_rl_name = kwargs.get("database_rl_name")
            table_name = kwargs.get("table_name")
            table_permissions = permissions
            glue = aws.GlueService()
            database = glue.get_database_detail(database_rl_name)
            database_name = database["TargetDatabase"]["DatabaseName"]
            lake_formation = aws.LakeFormationService()

            lake_formation.revoke_table_permissions(
                database=database_name,
                table=table_name,
                resource_catalog_id=resource_catalog_id,
                principal=principal,
                permissions=table_permissions,
            )

            messages.success(request, "Permissions Revoked.")
        except Exception as e:
            messages.error(request, f"Failed to revoke permissions: {str(e)}")

        return HttpResponseRedirect(
            reverse("poc:table_detail", args=[resource_catalog_id, database_rl_name, table_name])
        )
