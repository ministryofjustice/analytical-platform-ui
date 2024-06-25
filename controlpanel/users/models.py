from django.contrib.auth.models import AbstractUser
from django.db import models

from controlpanel.core.common.utils import sanitize_dns_label


class User(AbstractUser):
    user_id = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=256, blank=True)
    nickname = models.CharField(max_length=256, blank=True)

    REQUIRED_FIELDS = ["email", "user_id"]

    class Meta:
        db_table = "control_panel_user"
        ordering = ("name",)

    def __repr__(self):
        return f"<User: {self.username} ({self.user_id})>"

    def get_full_name(self):
        return self.name

    @staticmethod
    def construct_username(name):
        return sanitize_dns_label(name)

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
