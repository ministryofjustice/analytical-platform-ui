import botocore
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
        grantable_permissions: list | None = None,
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
            PermissionsWithGrantOption=grantable_permissions or [],
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
        except botocore.exceptions.ClientError as error:
            msg = error.response["Error"]["Message"]
            code = error.response["Error"]["Code"]
            if (
                code == "InvalidInputException"
                and "Grantee has no permissions and no grantable permissions on resource" in msg
            ):
                return logger.info(f"Nothing to revoke, continuing. Original exception: '{msg}'")
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
        try:
            client.revoke_permissions(
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
        except botocore.exceptions.ClientError as error:
            msg = error.response["Error"]["Message"]
            code = error.response["Error"]["Code"]
            if (
                code == "InvalidInputException"
                and "Grantee has no permissions and no grantable permissions on resource" in msg
            ):
                return logger.info(f"Nothing to revoke, continuing. Original exception: '{msg}'")
            sentry_sdk.capture_exception(error)
            raise error

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
        try:
            return client.create_lake_formation_opt_in(
                Principal={"DataLakePrincipalIdentifier": principal}, Resource=resource
            )
        except botocore.exceptions.ClientError as error:
            code = error.response["Error"]["Code"]
            msg = error.response["Error"]["Message"]
            if code == "InvalidInputException" and "already exists" in msg:
                logger.info("Lake Formation opt-in already exists, continuing")
                return
            raise error

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

        try:
            return client.delete_lake_formation_opt_in(
                Principal={"DataLakePrincipalIdentifier": principal}, Resource=resource
            )
        except botocore.exceptions.ClientError as error:
            msg = error.response["Error"]["Message"]
            code = error.response["Error"]["Code"]
            if code == "InvalidInputException" and "does not exist" in msg:
                return logger.info("Lake Formation opt-in does not exist, continuing")
            raise error

    def list_permissions(self, principal, resource):
        logger.info(f"Getting permissions for {principal} on {resource}")
        client = self.get_client()
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

    def list_object_permissions(self, resource_type, resource):
        logger.info(f"Getting permissions for {resource_type} on {resource}")
        client = self.get_client()
        response = client.list_permissions(ResourceType=resource_type, Resource=resource)

        result = []
        for permission in response.get("PrincipalResourcePermissions", []):
            principal_identifier = permission["Principal"]["DataLakePrincipalIdentifier"]
            user_permissions = permission["Permissions"]
            if "/users/" in principal_identifier:
                principal_name = principal_identifier.rsplit("/", 1)[-1]

                existing_permission = next(
                    (p for p in result if p["principal_name"] == principal_name), None
                )

                if existing_permission:
                    existing_permission["permissions"].extend(user_permissions)
                else:
                    result.append(
                        {
                            "principal": principal_identifier,
                            "principal_name": principal_name,
                            "permissions": user_permissions,
                        }
                    )

        return result
