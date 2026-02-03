"""Tests for the list command."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dubco_cli.main import app
from dubco_cli.models.link import Link


runner = CliRunner()


class TestListCommand:
    """Tests for the list command."""

    @patch("dubco_cli.commands.list.DubClient")
    @patch("dubco_cli.config.get_client_id")
    @patch("dubco_cli.config.load_credentials")
    def test_list_links_table_format(
        self, mock_creds, mock_client_id, mock_client_cls, sample_links_response
    ):
        """Should list links in table format."""
        mock_client_id.return_value = "test_client_id"
        mock_creds.return_value = MagicMock(
            access_token="test_token",
            expires_at=9999999999,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        mock_client.get.return_value = sample_links_response

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "dub.sh" in result.output

    @patch("dubco_cli.commands.list.DubClient")
    @patch("dubco_cli.config.get_client_id")
    @patch("dubco_cli.config.load_credentials")
    def test_list_links_json_format(
        self, mock_creds, mock_client_id, mock_client_cls, sample_links_response
    ):
        """Should list links in JSON format."""
        mock_client_id.return_value = "test_client_id"
        mock_creds.return_value = MagicMock(
            access_token="test_token",
            expires_at=9999999999,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        mock_client.get.return_value = sample_links_response

        result = runner.invoke(app, ["list", "--format", "json"])

        assert result.exit_code == 0
        assert '"shortLink"' in result.output

    def test_list_invalid_format(self):
        """Should error on invalid format."""
        result = runner.invoke(app, ["list", "--format", "invalid"])

        assert result.exit_code == 2
        assert "Invalid format" in result.output

    def test_list_invalid_sort(self):
        """Should error on invalid sort option."""
        result = runner.invoke(app, ["list", "--sort", "invalid"])

        assert result.exit_code == 2
        assert "Invalid sort" in result.output
