from django.db import transaction

from ap import aws
from ap.poc.models import RAMShare, SharedResource


@transaction.atomic
def create_or_update_ram_objects():
    ram_service = aws.RAMService()
    arns = []
    for resource_share in ram_service.get_resource_shares():
        arns.append(resource_share["resourceShareArn"])
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

    # remove cancelled ram shares
    delete_shared_resources(exclude_arns=arns)


def delete_shared_resources(exclude_arns):
    for ram_share in RAMShare.objects.exclude(arn__in=exclude_arns):
        ram_share.delete()


def create_or_update_shared_resources():
    ram_service = aws.RAMService()
    for resource in ram_service.list_all_resources():
        arn = resource["arn"]
        account_id = arn.split(":")[4]
        obj, created = SharedResource.objects.get_or_create(
            arn=resource["arn"],
            defaults={
                "resource_type": resource.get("type", ""),
                "account_id": account_id,
            },
        )
        if not created:
            continue

        if obj.resource_type in ["glue:Database"]:
            glue_service = aws.GlueService()
            glue_service.create_resource_link_database(resource)
