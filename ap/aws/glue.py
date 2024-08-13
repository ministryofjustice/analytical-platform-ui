from django.conf import settings

from . import base


class GlueService(base.AWSService):
    aws_service_name = "glue"

    def __init__(self, catalog_id=None):
        super().__init__()
        self.catalog_id = catalog_id or settings.GLUE_CATALOG_ID

    def get_database_list(self):
        databases = self._request("get_databases")
        if not databases:
            return []
        return databases["DatabaseList"]

    def get_table_list(self, database_name):
        tables = self._request("get_tables", CatalogId=self.catalog_id, DatabaseName=database_name)
        if not tables:
            return []
        return tables["TableList"]

    def get_table_detail(self, database_name, table_name):
        table = self._request(
            "get_table", CatalogId=self.catalog_id, DatabaseName=database_name, Name=table_name
        )
        if not table:
            return {}
        return table["Table"]
