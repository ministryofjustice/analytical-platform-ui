from functools import cached_property

from django.db import models, transaction
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel

from ap import aws


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

        # grant access
        lake_formation = aws.LakeFormationService()
        quicksight_user = lake_formation.arn(
            resource=f"user/default/{self.user.email}",
            service="quicksight",
        )
        lake_formation.grant_database_permissions(
            database=self.name, principal=quicksight_user, permissions=["DESCRIBE"]
        )
        super().save(*args, **kwargs)
        if create:
            self.access_levels.add(
                AccessLevel.objects.get_or_create(
                    name="DESCRIBE", entity=AccessLevel.Entity.DATABASE, grantable=False
                )[0]
            )

    def delete(self, *args, **kwargs):
        # revoke access
        lake_formation = aws.LakeFormationService()
        quicksight_user = lake_formation.arn(
            resource=f"user/default/{self.user.email}",
            service="quicksight",
        )
        lake_formation.revoke_database_permissions(database=self.name, principal=quicksight_user)
        super().delete(*args, **kwargs)


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

    @cached_property
    def table_details(self):
        """
        Returns information about the table from the Glue API, including the source catalog ID and
        source table that it belongs to. We could choose to store this informtion on the model to
        save API calls, as details that we need such as the database name and catalog ID do not
        change. But this would still be duplicated information so may not be worth it.
        """
        return aws.GlueService().get_table_detail(
            database_name=self.database_access.name, table_name=self.name
        )

    @cached_property
    def grantable_permissions(self):
        return list(self.access_levels.filter(grantable=True).values_list("name", flat=True))

    @cached_property
    def non_grantable_permissions(self):
        return list(self.access_levels.filter(grantable=False).values_list("name", flat=True))

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

    def save(self, **kwargs):
        # update LF access
        lake_formation = aws.LakeFormationService()
        quicksight_user = lake_formation.arn(
            resource=f"user/default/{self.database_access.user.email}",
            service="quicksight",
        )

        # if API call fails dont save the model
        with transaction.atomic():
            super().save(**kwargs)
            # there is no good way to check the region of the source (shared) table, so for now
            # assume that it will always be eu-west-1, as this is where data lives in the data-prod
            # account, and tables have to be shared to the same region. If data starts to be shared
            # from other accounts/regions we will need to think of a more dynamic solution eg. check
            # the catalog ID
            region_name = "eu-west-1"
            lake_formation.grant_table_permissions(
                # call glue API to get the name of the shared db. Alternatively we could infer it
                # based on what is implemented on the module that shares databases e.g. strip
                # _resource_link if present
                database=self.table_details["DatabaseName"],
                table=self.name,
                principal=quicksight_user,
                resource_catalog_id=self.table_details["CatalogId"],
                region_name=region_name,
                permissions=self.non_grantable_permissions,
                permissions_with_grant_option=self.grantable_permissions,
            )

    def delete(self, **kwargs):
        # update LF access
        lake_formation = aws.LakeFormationService()
        quicksight_user = lake_formation.arn(
            resource=f"user/default/{self.database_access.user.email}",
            service="quicksight",
        )

        # there is no good way to check the region of the source (shared) table, so for now assume
        # that it will always be eu-west-1, as this is where data lives in the data-prod account,
        # and tables have to be shared to the same region. If data starts to be shared from other
        # accounts/regions we will need to think of a more dynamic solution eg. check the catalog ID
        region_name = "eu-west-1"
        lake_formation.revoke_table_permissions(
            database=self.table_details["DatabaseName"],
            table=self.name,
            principal=quicksight_user,
            resource_catalog_id=self.table_details["CatalogId"],
            region_name=region_name,
        )

        super().delete(**kwargs)

        if not self.database_access.table_access.exists():
            # if this was the last table access for the database, revoke database access
            self.database_access.delete()
