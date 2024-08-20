from ap.aws.base import AWSService


class LakeFormationService(AWSService):
    aws_service_name = "lakeformation"

    def __init__(self, catalog_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.catalog_id = catalog_id or self.account_id
        self.clients = {}

    def grant_table_permissions(
        self,
        database: str,
        table: str,
        principal: str,
        catalog_id: str = "",
        resource_catalog_id: str = "",
        region_name: str = "",
    ):
        client = self.get_client(region_name)
        return client.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal},
            Resource={
                "Table": {
                    "DatabaseName": database,
                    "Name": table,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            },
            Permissions=["SELECT"],
            CatalogId=catalog_id or self.catalog_id,
        )

    def get_client(self, region_name: str = ""):
        region_name = region_name or self.region_name
        if region_name not in self.clients:
            self.clients[region_name] = self.boto3_session.client(
                "lakeformation", region_name=region_name
            )
        return self.clients[region_name]

    def grant_database_permissions(
        self,
        database: str,
        principal: str,
        region_name: str = "",
        catalog_id: str = "",
        resource_catalog_id: str = "",
    ):
        """
        Grant the principal permissions to the database.
        """
        client = self.get_client(region_name)
        return client.grant_permissions(
            Principal={"DataLakePrincipalIdentifier": principal},
            Resource={
                "Database": {
                    "Name": database,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            },
            Permissions=["DESCRIBE"],
            CatalogId=catalog_id or self.catalog_id,
        )
