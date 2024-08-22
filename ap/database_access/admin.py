from django.contrib import admin

from . import models


@admin.register(models.AccessLevel)
class AccessLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "entity", "grantable")
    ordering = ("name", "entity")
