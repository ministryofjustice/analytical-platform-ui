from django.db import transaction

from ap import aws
from ap.poc.models import RAMShare


@transaction.atomic
def create_or_update_ram_objects():
    ram_service = aws.RAMService()
    for resource_share in ram_service.get_resource_shares():
        obj, created = RAMShare.objects.get_or_create(
            arn=resource_share["resourceShareArn"],
            defaults={
                "name": resource_share["name"],
                "status": resource_share["status"],
                "account_id": resource_share["owningAccountId"],
            },
        )
        # if new object, create the resource link
        if created:
            obj.create_database_resource_link()
            continue

        # if nothing has changed since last run, do nothing
        if resource_share["lastUpdatedTime"] < obj.modified:
            continue

        # otherwise update the object in the DB, and update resource links? TBC
        obj.status = resource_share["status"]
        obj.account_id = resource_share["owningAccountId"]
        obj.save()
        # obj.update_resource_links()
