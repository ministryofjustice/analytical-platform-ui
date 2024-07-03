from django.db import models

from django_extensions.db.models import TimeStampedModel


class Approver(TimeStampedModel, models.Model):
    email = models.EmailField(null=True, blank=True)
    user = models.ForeignKey(to="users.User", on_delete=models.CASCADE)
