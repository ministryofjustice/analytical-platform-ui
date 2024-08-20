from unittest.mock import Mock, patch

import pytest

from ap.aws.quicksight import QuicksightService


class TestQuickSightService:

    @pytest.fixture
    def quicksight_service(self):
        yield QuicksightService()

    def test_get_embed_url(self, quicksight_service):
        """
        Patching request as no way to get url from moto.
        Should return some URL anyway
        """
        embedded_url = "https://embedded-url.com"

        with patch.object(quicksight_service, "_request", return_value={"EmbedUrl": embedded_url}):
            mock_user = Mock(email="user@email.com")
            url = quicksight_service.get_embed_url(mock_user)
            assert url == embedded_url
