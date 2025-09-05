from unittest.mock import MagicMock, patch

from django.conf import settings

from ap.aws.ram import RAMService


class TestRAMService:
    """Test suite for RAMService."""

    def test_aws_service_name(self):
        """Test that RAMService has correct AWS service name."""
        service = RAMService()
        assert service.aws_service_name == "ram"

    def test_get_resource_shares_returns_generator(self):
        """Test that get_resource_shares returns a generator."""
        service = RAMService()
        result = service.get_resource_shares()

        # Check it's a generator
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    @patch("ap.aws.ram.RAMService.client")
    def test_get_resource_shares_filters_lakeformation_shares(self, mock_client):
        """Test that get_resource_shares only returns LakeFormation-V4 shares."""
        # Mock paginator and page data
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_pages = [
            {
                "resourceShares": [
                    {
                        "name": "LakeFormation-V4-TestShare1",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                        "status": "ACTIVE",
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    },
                    {
                        "name": "OtherShare-NotLakeFormation",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/other-share",  # noqa
                        "status": "ACTIVE",
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    },
                    {
                        "name": "LakeFormation-V4-TestShare2",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-2",  # noqa
                        "status": "PENDING",
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    },
                ]
            }
        ]
        mock_paginator.paginate.return_value = mock_pages

        service = RAMService()
        results = list(service.get_resource_shares())

        # Should only return LakeFormation-V4 shares
        assert len(results) == 2
        assert all(share["name"].startswith("LakeFormation-V4") for share in results)
        assert results[0]["name"] == "LakeFormation-V4-TestShare1"
        assert results[1]["name"] == "LakeFormation-V4-TestShare2"

    @patch("ap.aws.ram.RAMService.client")
    def test_get_resource_shares_default_kwargs(self, mock_client):
        """Test that get_resource_shares sets correct default kwargs."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"resourceShares": []}]

        service = RAMService()
        list(service.get_resource_shares())  # Consume generator

        # Verify paginate was called with correct defaults
        mock_paginator.paginate.assert_called_once_with(
            resourceOwner="OTHER-ACCOUNTS",
            resourceShareStatus="ACTIVE",
            PaginationConfig={"PageSize": 100},
        )

    @patch("ap.aws.ram.RAMService.client")
    def test_get_resource_shares_custom_kwargs(self, mock_client):
        """Test that get_resource_shares accepts custom kwargs."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"resourceShares": []}]

        service = RAMService()
        custom_kwargs = {
            "resourceOwner": "SELF",
            "resourceShareStatus": "PENDING",
            "maxResults": 50,
        }
        list(service.get_resource_shares(**custom_kwargs))

        # Verify custom kwargs were passed through
        expected_kwargs = custom_kwargs.copy()
        expected_kwargs["PaginationConfig"] = {"PageSize": 100}
        mock_paginator.paginate.assert_called_once_with(**expected_kwargs)

    @patch("ap.aws.ram.RAMService.client")
    def test_get_resource_shares_handles_empty_pages(self, mock_client):
        """Test that get_resource_shares handles pages with no resourceShares."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_pages = [
            {},  # Empty page
            {"resourceShares": []},  # Page with empty list
            {
                "resourceShares": [
                    {
                        "name": "LakeFormation-V4-TestShare1",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    }
                ]
            },
        ]
        mock_paginator.paginate.return_value = mock_pages

        service = RAMService()
        results = list(service.get_resource_shares())

        assert len(results) == 1
        assert results[0]["name"] == "LakeFormation-V4-TestShare1"

    def test_list_resources_returns_generator(self):
        """Test that list_resources returns a generator."""
        service = RAMService()
        result = service.list_resources(["arn:aws:ram:eu-west-2:123456789012:resource-share/test"])

        # Check it's a generator
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    @patch("ap.aws.ram.RAMService.client")
    def test_list_resources_with_resource_share_arns(self, mock_client):
        """Test list_resources with resource share ARNs."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_pages = [
            {
                "resources": [
                    {
                        "arn": "arn:aws:glue:eu-west-2:123456789012:table/test_database/test_table_1",  # noqa
                        "type": "glue:Table",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                        "status": "AVAILABLE",
                    },
                    {
                        "arn": "arn:aws:glue:eu-west-2:123456789012:database/test_database",
                        "type": "glue:Database",
                        "resourceShareArn": "arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1",  # noqa
                        "status": "AVAILABLE",
                    },
                ]
            }
        ]
        mock_paginator.paginate.return_value = mock_pages

        service = RAMService()
        resource_share_arns = ["arn:aws:ram:eu-west-2:123456789012:resource-share/test-share-1"]
        results = list(service.list_resources(resource_share_arns))

        assert len(results) == 2
        assert results[0]["type"] == "glue:Table"
        assert results[1]["type"] == "glue:Database"
        assert all(resource["resourceShareArn"] == resource_share_arns[0] for resource in results)

    @patch("ap.aws.ram.RAMService.client")
    def test_list_resources_default_kwargs(self, mock_client):
        """Test that list_resources sets correct default kwargs."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"resources": []}]

        service = RAMService()
        resource_share_arns = ["arn:aws:ram:eu-west-2:123456789012:resource-share/test"]
        list(service.list_resources(resource_share_arns))

        # Verify paginate was called with correct defaults
        mock_paginator.paginate.assert_called_once_with(
            resourceShareArns=resource_share_arns,
            resourceOwner="OTHER-ACCOUNTS",
            PaginationConfig={"PageSize": 100},
        )

    @patch("ap.aws.ram.RAMService.client")
    def test_list_resources_custom_kwargs(self, mock_client):
        """Test that list_resources accepts custom kwargs."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"resources": []}]

        service = RAMService()
        resource_share_arns = ["arn:aws:ram:eu-west-2:123456789012:resource-share/test"]
        custom_kwargs = {"resourceOwner": "SELF", "resourceType": "glue:Table"}
        list(service.list_resources(resource_share_arns, **custom_kwargs))

        # Verify custom kwargs were passed through
        expected_kwargs = {
            "resourceShareArns": resource_share_arns,
            "resourceOwner": "SELF",
            "resourceType": "glue:Table",
            "PaginationConfig": {"PageSize": 100},
        }
        mock_paginator.paginate.assert_called_once_with(**expected_kwargs)

    @patch("ap.aws.ram.RAMService.client")
    def test_list_resources_handles_empty_pages(self, mock_client):
        """Test that list_resources handles pages with no resources."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_pages = [
            {},  # Empty page
            {"resources": []},  # Page with empty list
            {
                "resources": [
                    {
                        "arn": "arn:aws:glue:eu-west-2:123456789012:table/test_database/test_table_1",  # noqa
                        "type": "glue:Table",
                    }
                ]
            },
        ]
        mock_paginator.paginate.return_value = mock_pages

        service = RAMService()
        resource_share_arns = ["arn:aws:ram:eu-west-2:123456789012:resource-share/test"]
        results = list(service.list_resources(resource_share_arns))

        assert len(results) == 1
        assert results[0]["type"] == "glue:Table"

    @patch("ap.aws.ram.RAMService.client")
    def test_list_resources_empty_arn_list(self, mock_client):
        """Test list_resources with empty resource share ARN list."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"resources": []}]

        service = RAMService()
        results = list(service.list_resources([]))

        assert len(results) == 0
        # Should still call paginate with empty list
        mock_paginator.paginate.assert_called_once_with(
            resourceShareArns=[], resourceOwner="OTHER-ACCOUNTS", PaginationConfig={"PageSize": 100}
        )

    @patch("ap.aws.ram.RAMService.client")
    def test_generator_lazy_evaluation(self, mock_client):
        """Test that generators provide lazy evaluation."""
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        # Mock multiple pages to test lazy loading
        mock_pages = [
            {
                "resourceShares": [
                    {
                        "name": "LakeFormation-V4-Share1",
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    }
                ]
            },
            {
                "resourceShares": [
                    {
                        "name": "LakeFormation-V4-Share2",
                        "owningAccountId": settings.PRODUCER_ACCOUNT_ID,
                    }
                ]
            },
        ]
        mock_paginator.paginate.return_value = iter(mock_pages)

        service = RAMService()
        generator = service.get_resource_shares()

        # Paginate should not be called until we start iterating
        mock_paginator.paginate.assert_not_called()

        # Get first item
        first_item = next(generator)
        assert first_item["name"] == "LakeFormation-V4-Share1"

        # Now paginate should have been called
        mock_paginator.paginate.assert_called_once()
