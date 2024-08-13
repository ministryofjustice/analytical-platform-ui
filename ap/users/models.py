from django.conf import settings
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

    @staticmethod
    def construct_username(name):
        return sanitize_dns_label(name)

    @property
    def quicksight_arn(self):
        return (
            f"arn:aws:quicksight:eu-west-2:{settings.COMPUTE_ACCOUNT_ID}:user/default/{self.email}"
        )

    @property
    def display_first_name(self):
        if self.first_name:
            return self.first_name.title()

        return self.name.split(",")[-1].title()

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
