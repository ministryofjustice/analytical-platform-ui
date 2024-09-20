from unittest.mock import MagicMock, patch

import botocore
import botocore.exceptions
import pytest

from ap.aws.lakeformation import LakeFormationService


class TestRevoke:
    def test_revoke_database_no_error(self):
        """
        Test that if the user does not have access to revoke, no error is raised
        """
        lf = LakeFormationService()
        with patch.object(lf, "get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.revoke_permissions.side_effect = botocore.exceptions.ClientError(
                {
                    "Error": {
                        "Code": "InvalidInputException",
                        "Message": "Grantee has no permissions and no grantable permissions on resource",  # noqa
                    }
                },
                "revoke_permissions",
            )
            mock_get_client.return_value = mock_client
            assert (
                lf.revoke_database_permissions(database="db_without_access", principal="user")
                is None
            )

    def test_revoke_database_raises_error(self):
        lf = LakeFormationService()
        with patch.object(lf, "get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.revoke_permissions.side_effect = botocore.exceptions.ClientError(
                {
                    "Error": {
                        "Code": "SomeOtherError",
                        "Message": "Some other error message",
                    }
                },
                "revoke_permissions",
            )
            mock_get_client.return_value = mock_client
            # revoking should raises exception
            with pytest.raises(botocore.exceptions.ClientError):
                lf.revoke_database_permissions(database="db_without_access", principal="user")

    def test_revoke_table_no_error(self):
        """
        Test that if the user does not have access to revoke, no error is raised
        """
        lf = LakeFormationService()
        with patch.object(lf, "get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.revoke_permissions.side_effect = botocore.exceptions.ClientError(
                {
                    "Error": {
                        "Code": "InvalidInputException",
                        "Message": "Grantee has no permissions and no grantable permissions on resource",  # noqa
                    }
                },
                "revoke_permissions",
            )
            mock_get_client.return_value = mock_client
            assert (
                lf.revoke_table_permissions(
                    database="db_without_access", table="table_without_access", principal="user"
                )
                is None
            )

    def test_revoke_table_raises_error(self):
        lf = LakeFormationService()
        with patch.object(lf, "get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.revoke_permissions.side_effect = botocore.exceptions.ClientError(
                {
                    "Error": {
                        "Code": "SomeOtherError",
                        "Message": "Some other error message",
                    }
                },
                "revoke_permissions",
            )
            mock_get_client.return_value = mock_client
            # revoking should raises exception
            with pytest.raises(botocore.exceptions.ClientError):
                lf.revoke_table_permissions(
                    database="db_without_access", table="table_without_access", principal="user"
                )
