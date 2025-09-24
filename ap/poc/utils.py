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


def transform_database(database):
    db = {
        "rl_name": database["Name"],
        "rl_catalog_id": database["CatalogId"],
    }

    if "TargetDatabase" in database:
        db["name"] = database["TargetDatabase"]["DatabaseName"]
        db["catalog_id"] = database["TargetDatabase"]["CatalogId"]
    else:
        db["name"] = database["Name"]
        db["catalog_id"] = database["CatalogId"]

    return db


def transform_database_list(databases):
    db_list = []
    for db in databases:
        db_list.append(transform_database(db))

    return db_list


def transform_table(table):
    tbl = {
        "rl_name": table["Name"],
        "rl_catalog_id": table["CatalogId"],
        "created": table["CreateTime"],
        "lf_registerd": table["IsRegisteredWithLakeFormation"],
    }

    if "TargetTable" in table:
        tbl["name"] = table["TargetTable"]["Name"]
        tbl["catalog_id"] = table["TargetTable"]["CatalogId"]
        tbl["original_database_name"] = table["TargetTable"]["DatabaseName"]
    else:
        tbl["name"] = table["Name"]
        tbl["catalog_id"] = table["CatalogId"]

    return tbl


def transform_table_list(tables):
    table_list = []
    for table in tables:
        table_list.append(transform_table(table))

    return table_list
