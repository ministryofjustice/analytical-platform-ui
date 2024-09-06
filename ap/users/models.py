from django.contrib.auth.models import AbstractUser
from django.db import models

from ap.core.utils import sanitize_dns_label


class User(AbstractUser):
    user_id = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=256, blank=True)
    nickname = models.CharField(max_length=256, blank=True)

    REQUIRED_FIELDS = ["email", "user_id"]

    class Meta:
        db_table = "ap_user"
        ordering = ("name",)

    def __repr__(self):
        return f"<User: {self.username} ({self.user_id})>"

    def __str__(self) -> str:
        return self.email

    @staticmethod
    def construct_username(name):
        return sanitize_dns_label(name)

    @property
    def display_first_name(self):
        if self.first_name:
            return self.first_name.title()

        return self.name.split(",")[-1].title()

    def can_manage_access(self, database_name, table_name):
        """
        Check if the user has permission to manage access to the table.
        Returns True if the user is a superuser or has grantable permissions on the table.
        """
        if self.is_superuser:
            return True

        db = self.database_access.filter(name=database_name).first()
        if not db:
            return False

        table_access = db.table_access.filter(name=table_name).first()
        if not table_access:
            return False

        return table_access.grantable_permissions.exists()

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
