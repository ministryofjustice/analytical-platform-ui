import sentry_sdk
import structlog

from ap.aws.base import AWSService

logger = structlog.get_logger(__name__)


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
        permissions: list | None = None,
        permissions_with_grant_option: list | None = None,
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
            CatalogId=catalog_id or self.catalog_id,
            Permissions=permissions or [],
            # TODO grantable permissions must also be in the standard permissions list, so need a
            # solution for this
            PermissionsWithGrantOption=permissions_with_grant_option or [],
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
        permissions: list | None = None,
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
            Permissions=permissions or ["DESCRIBE"],
            CatalogId=catalog_id or self.catalog_id,
        )

    def revoke_table_permissions(
        self,
        database: str,
        table: str,
        principal: str,
        resource_catalog_id: str = "",
        region_name: str = "",
        permissions: list | None = None,
        grantable_permissions: list | None = None,
    ):
        client = self.get_client(region_name)
        resource = {
            "Table": {
                "DatabaseName": database,
                "Name": table,
                "CatalogId": resource_catalog_id or self.catalog_id,
            },
        }
        try:
            return client.revoke_permissions(
                Principal={"DataLakePrincipalIdentifier": principal},
                Resource=resource,
                Permissions=permissions or [],
                PermissionsWithGrantOption=grantable_permissions or [],
            )
        except client.exceptions.InvalidInputException as error:
            sentry_sdk.capture_exception(error)
            logger.info(f"Error revoking permissions for {principal}", error=error)
            raise error

    def revoke_database_permissions(
        self,
        database: str,
        principal: str,
        region_name: str = "",
        catalog_id: str = "",
        resource_catalog_id: str = "",
        permissions: list | None = None,
    ):
        """
        Grant the principal permissions to the database.
        """
        client = self.get_client(region_name)
        return client.revoke_permissions(
            Principal={"DataLakePrincipalIdentifier": principal},
            Resource={
                "Database": {
                    "Name": database,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            },
            Permissions=permissions or ["DESCRIBE"],
            CatalogId=catalog_id or self.catalog_id,
        )

    def create_lake_formation_opt_in(
        self,
        database: str,
        principal: str,
        table: str = "",
        resource_catalog_id: str = "",
        region_name: str = "",
    ):
        client = self.get_client(region_name or "eu-west-1")
        if table:
            resource = {
                "Table": {
                    "DatabaseName": database,
                    "Name": table,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            }
        else:
            resource = {
                "Database": {
                    "Name": database,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            }

        client.create_lake_formation_opt_in(
            Principal={"DataLakePrincipalIdentifier": principal}, Resource=resource
        )

    def delete_lake_formation_opt_in(
        self,
        database: str,
        principal: str,
        table: str = "",
        resource_catalog_id: str = "",
        region_name: str = "",
    ):
        client = self.get_client(region_name or "eu-west-1")
        if table:
            resource = {
                "Table": {
                    "DatabaseName": database,
                    "Name": table,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            }
        else:
            resource = {
                "Database": {
                    "Name": database,
                    "CatalogId": resource_catalog_id or self.catalog_id,
                },
            }

        client.delete_lake_formation_opt_in(
            Principal={"DataLakePrincipalIdentifier": principal}, Resource=resource
        )

    def list_permissions(self, principal, resource):
        logger.info(f"Getting permissions for {principal} on {resource}")
        client = self.get_client(region_name="eu-west-1")
        response = client.list_permissions(
            Principal={"DataLakePrincipalIdentifier": principal}, Resource=resource
        )
        permissions = response["PrincipalResourcePermissions"]

        if not permissions:
            return None

        return {
            "Permissions": response["PrincipalResourcePermissions"][0]["Permissions"],
            "PermissionsWithGrantOption": response["PrincipalResourcePermissions"][0][
                "PermissionsWithGrantOption"
            ],
        }
