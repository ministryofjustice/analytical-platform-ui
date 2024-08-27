from django.db import models
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel


class AccessLevel(models.Model):
    class Entity(models.TextChoices):
        DATABASE = "database", "Database"
        TABLE = "table", "Table"

    name = models.CharField(max_length=255)
    entity = models.CharField(max_length=255, choices=Entity.choices)
    grantable = models.BooleanField(default=False)

    def __str__(self):
        grantable = "grantable" if self.grantable else "not grantable"
        return f"{self.name} ({self.entity}, {grantable})"

    class Meta:
        ordering = ("name", "entity")
        unique_together = ("name", "entity", "grantable")


class DatabaseAccess(TimeStampedModel):
    user = models.ForeignKey("users.User", related_name="database_access", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    access_levels = models.ManyToManyField(
        "AccessLevel",
        related_name="database_access",
        limit_choices_to={"entity": AccessLevel.Entity.DATABASE},
    )

    class Meta:
        unique_together = ("user", "name")

    def save(self, *args, **kwargs):
        create = self.pk is None
        super().save(*args, **kwargs)
        if create:
            self.access_levels.add(
                AccessLevel.objects.get_or_create(
                    name="DESCRIBE", entity=AccessLevel.Entity.DATABASE, grantable=False
                )[0]
            )


class TableAccess(TimeStampedModel):
    database_access = models.ForeignKey(
        "database_access.DatabaseAccess",
        related_name="table_access",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    access_levels = models.ManyToManyField(
        "AccessLevel",
        related_name="table_access",
        limit_choices_to={"entity": AccessLevel.Entity.TABLE},
    )

    class Meta:
        unique_together = ("database_access", "name")

    def get_absolute_url(self, viewname: str = "database_access:manage_table_access"):
        return reverse(
            viewname=viewname,
            kwargs={
                "database_name": self.database_access.name,
                "table_name": self.name,
                "pk": self.pk,
            },
        )

    def get_absolute_revoke_url(self):
        return self.get_absolute_url(viewname="database_access:revoke_table_access")
