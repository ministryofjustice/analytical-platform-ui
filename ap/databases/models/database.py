from django.db import models

from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import TimeStampedModel


class Database(TimeStampedModel, models.Model):
    # TODO add validation
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name")

    def __str__(self) -> str:
        return self.name
