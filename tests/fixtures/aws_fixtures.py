# Standard library
import json
import os

# Third-party
import boto3
import moto
import pytest
from django.conf import settings


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
        yield boto3.client("sts")


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


        glue = boto3.client("glue")

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
        lake_formation = boto3.client("lakeformation")
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
def quicksight(aws_creds):
    with moto.mock_aws():
        yield boto3.client("quicksight", region_name="eu-west-2")
