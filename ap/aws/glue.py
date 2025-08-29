from . import base


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
