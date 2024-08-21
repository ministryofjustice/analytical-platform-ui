from django.conf import settings

import pytest

from ap.aws.glue import GlueService


class TestGlueService:

    @pytest.fixture
    def glue_service(self):
        yield GlueService(settings.GLUE_CATALOG_ID)

    def test_get_database_list(self, glue_service):
        databases = glue_service.get_database_list()

        assert len(databases) == 2

    @pytest.mark.parametrize(
        "database_name,expected_table_count",
        [
            ("test_database", 2),
            ("test_database_2", 1),
        ],
    )
    def test_get_table_list(self, glue_service, database_name, expected_table_count):
        tables = glue_service.get_table_list(database_name)
        assert len(tables) == expected_table_count

    def test_get_table_detail(self, glue_service):
        db_name = "test_database"
        table_name = "test_table_1"
        table = glue_service.get_table_detail(db_name, table_name)

        assert table["Name"] == table_name

    @pytest.mark.parametrize(
        "resource,service,region_name,account_id,expected_arn",
        [
            ("resource", "", "", "", "arn:aws:glue:eu-west-2:123456789012:resource"),
            ("resource", "service", "", "", "arn:aws:service:eu-west-2:123456789012:resource"),
            (
                "resource",
                "service",
                "region_name",
                "",
                "arn:aws:service:region_name:123456789012:resource",
            ),
            (
                "resource",
                "service",
                "region_name",
                "account_id",
                "arn:aws:service:region_name:account_id:resource",
            ),
        ],
    )
    def test_arn(self, glue_service, resource, service, region_name, account_id, expected_arn):
        arn = glue_service.arn(resource, service, region_name, account_id)
        assert arn == expected_arn
