import structlog
from django.db import models, transaction
from django.urls import reverse
from django_extensions.db.models import TimeStampedModel

from ap import aws

logger = structlog.get_logger()


class RAMShare(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "PENDING"
        ACTIVE = "ACTIVE", "ACTIVE"
        FAILED = "FAILED", "FAILED"
        DELETING = "DELETING", "DELETING"
        DELETED = "DELETED", "DELETED"

    name = models.CharField(max_length=256, help_text="Resource Share Name")
    arn = models.CharField(max_length=512, unique=True, help_text="Resource Share ARN")
    status = models.CharField(
        max_length=64, choices=Status, help_text="Status of the Resource Share"
    )
    account_id = models.CharField(max_length=12, help_text="AWS Account ID")

    class Meta(TimeStampedModel.Meta):
        pass

    def __str__(self) -> str:
        return super().__str__()

    @property
    def ram_share_status_class(self):
        return {
            self.Status.PENDING: "govuk-tag--yellow",
            self.Status.ACTIVE: "govuk-tag--green",
            self.Status.FAILED: "govuk-tag--red",
            self.Status.DELETING: "govuk-tag--orange",
            self.Status.DELETED: "govuk-tag--grey",
        }.get(self.status, "")

    def get_absolute_url(self):
        return reverse("poc:resources", kwargs={"pk": self.pk})

    def get_shared_resources(self) -> list:
        return aws.RAMService().list_resources([self.arn])

    def create_database_resource_link(self):
        glue_service = aws.GlueService()
        for resource in self.get_shared_resources():
            if resource.get("type") != "glue:Database":
                continue
            try:
                glue_service.create_resource_link_database(resource)
            except glue_service.client.exceptions.AlreadyExistsException as err:
                print(f"Resource link already exists: {err}")
                continue

    @transaction.atomic
    def delete(self):
        glue_service = aws.GlueService()
        for resource in self.get_shared_resources():
            if resource.get("type") != "glue:Database":
                continue
            try:
                glue_service.delete_resource_link_database(resource)
            except glue_service.client.exceptions.EntityNotFoundException as err:
                logger.info(f"Resource link not found: {err}")
        return super().delete()
