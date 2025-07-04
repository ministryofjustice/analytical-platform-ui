import datetime
from unittest.mock import patch

import pytest

from ap.aws.session import BotoSession


class TestBotoSession:
    @pytest.fixture
    def boto_session(self):
        yield BotoSession()

    def test_refreshable_credentials(self, boto_session):
        credentials = boto_session.refreshable_credentials()

        assert hasattr(credentials, "access_key")
        assert hasattr(credentials, "secret_key")
        assert hasattr(credentials, "token")

    def test_get_sts_credentials(self, boto_session):
        expected_response = {
            "Credentials": {
                "AccessKeyId": "AccessKeyId",
                "SecretAccessKey": "ABC123",
                "SessionToken": "Token123",
                "Expiration": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
            }
        }

        with patch("ap.aws.session.boto3.Session.client") as mock_boto_client:
            mock_sts = mock_boto_client.return_value
            mock_sts.assume_role.return_value = expected_response

            credentials = boto_session.get_sts_credentials()

            assert credentials["access_key"] == expected_response["Credentials"]["AccessKeyId"]
            assert credentials["secret_key"] == expected_response["Credentials"]["SecretAccessKey"]
            assert credentials["token"] == expected_response["Credentials"]["SessionToken"]
            assert (
                credentials["expiry_time"]
                == expected_response["Credentials"]["Expiration"].isoformat()
            )
