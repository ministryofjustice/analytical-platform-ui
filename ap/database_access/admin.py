from django.contrib import admin

from . import models


@admin.register(models.Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "entity", "display_name")
    ordering = ("name", "entity")
