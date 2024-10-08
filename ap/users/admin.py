from django.contrib import admin

from . import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "user_id", "name", "is_superuser")
    exclude = ["password"]
