import structlog

from . import base

logger = structlog.get_logger(__name__)


class GlueService(base.AWSService):
    aws_service_name = "glue"

    def __init__(self, catalog_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_id = catalog_id or self.account_id

    def get_database_list(self, catalog_id=None):
        databases = self._request("get_databases", CatalogId=catalog_id or self.catalog_id)

        if not databases:
            return []
        return databases["DatabaseList"]

    def get_table_list(self, database_name, catalog_id=None):
        tables = self._request(
            "get_tables", CatalogId=catalog_id or self.catalog_id, DatabaseName=database_name
        )
        if not tables:
            return []
        return tables["TableList"]

    def get_table_detail(self, database_name, table_name, catalog_id=None):
        table = self._request(
            "get_table",
            CatalogId=catalog_id or self.catalog_id,
            DatabaseName=database_name,
            Name=table_name,
        )
        if not table:
            return {}
        return table["Table"]

    def get_database_detail(self, database_name, catalog_id=None):
        database = self._request(
            "get_database", CatalogId=catalog_id or self.catalog_id, Name=database_name
        )
        if not database:
            return {}
        return database["Database"]

    def get_database_for_grant(self, database_name, catalog_id=None):
        database = self.get_database_detail(database_name, catalog_id=catalog_id)
        if "TargetDatabase" in database:
            return database["TargetDatabase"]
        return database

    def create_database(self, database_name=None, **kwargs):
        kwargs = kwargs or {}
        kwargs.setdefault("CatalogId", self.catalog_id)
        kwargs.setdefault("DatabaseInput", {"Name": database_name})
        response = self.client.create_database(**kwargs)
        return response

    def create_resource_link_database(self, resource):
        """
        Create a resource link database in Glue.

        Example resource:
            {
            "arn": "arn:aws:glue:eu-west-2:720819236209:database/moj",
            "type": "glue:Database",
            "resourceShareArn": "arn:aws:ram:eu-west-2:720819236209:resource-share/ecdbb681-3639-4c7f-9cae-f51800033ba9",
            "status": "AVAILABLE",
            "creationTime": datetime.datetime(2025, 8, 28, 7, 19, 3, 459000, tzinfo=tzlocal()),
            "lastUpdatedTime": datetime.datetime(2025, 8, 28, 7, 19, 6, 330000, tzinfo=tzlocal()),
            "resourceRegionScope": "REGIONAL",
        }
        """  # noqa
        if resource.get("type") != "glue:Database":
            raise ValueError("Resource must be a Glue Database")

        arn = resource.get("arn")
        if not arn:
            raise ValueError("Resource ARN is required")

        account_id = arn.split(":")[4]
        database_name = arn.split("/")[-1]
        region_name = arn.split(":")[3]

        target_database = {
            "CatalogId": account_id,
            "DatabaseName": database_name,
            "Region": region_name,
        }
        resource_link_name = f"{account_id}_{database_name}"
        try:
            response = self.create_database(
                DatabaseInput={
                    "Name": resource_link_name,
                    "TargetDatabase": target_database,
                },
            )
        except self.client.exceptions.AlreadyExistsException:
            return logger.info(f"Resource link already exists for {resource_link_name}")
        return response
