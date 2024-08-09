from django.conf import settings

import botocore
import sentry_sdk

from . import base


class GlueService(base.AWSService):
    aws_service_name = "glue"

    def __init__(self, catalog_id=None):
        super().__init__()
        self.catalog_id = catalog_id or settings.GLUE_CATALOG_ID

    def get_table_list(self, database_name):
        try:
            tables = self.client.get_tables(
                CatalogId=self.catalog_id,
                DatabaseName=database_name,
            )["TableList"]
        except botocore.exceptions.ClientError as e:
            if settings.DEBUG:
                raise e
            sentry_sdk.capture_exception(e)
            tables = []

        return tables

    def get_table_detail(self, database_name, table_name):
        try:
            response = self.client.get_table(
                CatalogId=self.catalog_id,
                DatabaseName=database_name,
                Name=table_name,
            )
            table = response["Table"]
        except botocore.exceptions.ClientError as e:
            if settings.DEBUG:
                raise e
            sentry_sdk.capture_exception(e)
            table = {}

        return table
