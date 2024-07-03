from django.db import models

from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import TimeStampedModel


class Project(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from="name")
    review_date = models.DateField()
    business_case = models.TextField()
    databases = models.ManyToManyField(to="databases.Database")
    approver = models.ForeignKey(to="databases.Approver", null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.name
