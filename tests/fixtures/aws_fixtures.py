# Standard library
import os
from datetime import UTC, datetime

# Third-party
import boto3
import moto
import pytest


@pytest.fixture(autouse=True)
def aws_creds():
    os.environ["AWS_ACCESS_KEY_ID"] = "test-access-key-id"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret-access-key"
    os.environ["AWS_SECURITY_TOKEN"] = "test-security-token"
    os.environ["AWS_SESSION_TOKEN"] = "test-session-token"


@pytest.fixture(autouse=True)
def iam(aws_creds):
    with moto.mock_aws():
        yield boto3.Session().resource("iam")


@pytest.fixture(autouse=True)
def sts(aws_creds):
    with moto.mock_aws():
        yield boto3.client("sts", region_name="eu-west-2")


@pytest.fixture(autouse=True)
def glue(aws_creds):
    with moto.mock_aws():
        databases = ["test_database", "test_database_2"]
        external_db_name = "external_db"
        tables = [
            {
                "database": databases[0],
                "table_input": {
                    "Name": "test_table_1",
                    "TargetTable": {
                        "CatalogId": "123",
                        "DatabaseName": external_db_name,
                        "Name": "external_test_table",
                        "Region": "eu-west-2",
                    },
                },
            },
            {
                "database": databases[0],
                "table_input": {
                    "Name": "test_table_2",
                    "TargetTable": {
                        "CatalogId": "123",
                        "DatabaseName": external_db_name,
                        "Name": "external_test_table_2",
                        "Region": "eu-west-2",
                    },
                },
            },
            {
                "database": databases[1],
                "table_input": {
                    "Name": "test_table_3",
                },
            },
        ]

        glue = boto3.client("glue", region_name="eu-west-2")

        for db_name in databases:
            glue.create_database(DatabaseInput={"Name": db_name})

        for table in tables:
            glue.create_table(
                DatabaseName=table["database"],
                TableInput=table["table_input"],
            )

        yield glue


@pytest.fixture(autouse=True)
def lake_formation(aws_creds):
    with moto.mock_aws():
        lake_formation = boto3.client("lakeformation", region_name="eu-west-2")
        lake_formation.grant_permissions(
            Permissions=["DESCRIBE"],
            Principal={
                "DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/test_user_carol"
            },
            Resource={
                "Table": {
                    "CatalogId": "123456789012",
                    "DatabaseName": "test_database",
                    "Name": "test_table",
                },
            },
        )
        lake_formation.grant_permissions(
            Permissions=["SELECT"],
            Principal={
                "DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/test_user_carol"
            },
            Resource={
                "Table": {
                    "CatalogId": "123",
                    "DatabaseName": "external_db",
                    "Name": "external_test_table",
                },
            },
        )
        yield lake_formation


@pytest.fixture(autouse=True)
def ram(aws_creds):
    with moto.mock_aws():
        ram_client = boto3.client("ram", region_name="eu-west-2")

        # Create sample resource shares
        sample_shares = [
            {
                "name": "LakeFormation-V4-TestShare1",
                "owningAccountId": "123456789012",
                "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                "status": "ACTIVE",
                "lastUpdatedTime": datetime.now(UTC),
                "creationTime": datetime.now(UTC),
            },
            {
                "name": "LakeFormation-V4-TestShare2",
                "owningAccountId": "123456789012",
                "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-2",  # noqa
                "status": "PENDING",
                "lastUpdatedTime": datetime.now(UTC),
                "creationTime": datetime.now(UTC),
            },
            {
                "name": "OtherShare-NotLakeFormation",
                "owningAccountId": "123456789012",
                "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/other-share",
                "status": "ACTIVE",
                "lastUpdatedTime": datetime.now(UTC),
                "creationTime": datetime.now(UTC),
            },
        ]

        # Mock the resource shares data
        ram_client._sample_shares = sample_shares

        # Create sample resources for the shares
        sample_resources = [
            {
                "arn": "arn:aws:glue:eu-west-2:123456789012:table/test_database/test_table_1",
                "type": "glue:Table",
                "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                "status": "AVAILABLE",
                "creationTime": datetime.now(UTC),
                "lastUpdatedTime": datetime.now(UTC),
                "resourceRegionScope": "REGIONAL",
            },
            {
                "arn": "arn:aws:glue:eu-west-2:123456789012:database/test_database",
                "type": "glue:Database",
                "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                "creationTime": datetime.now(UTC),
                "lastUpdatedTime": datetime.now(UTC),
                "resourceRegionScope": "REGIONAL",
            },
        ]

        ram_client._sample_resources = sample_resources

        yield ram_client
