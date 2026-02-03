"""Tests for the add command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dubco_cli.main import app
from dubco_cli.models.link import CreateLinkRequest
from dubco_cli.utils.utm import extract_utm_from_url, merge_utm_params


runner = CliRunner()


class TestUTMHandling:
    """Tests for UTM parameter handling."""

    def test_extract_utm_from_url_with_params(self):
        """Should extract UTM params from URL."""
        url = "https://example.com?utm_source=twitter&utm_campaign=launch&other=keep"
        clean_url, utm = extract_utm_from_url(url)

        assert clean_url == "https://example.com?other=keep"
        assert utm["utm_source"] == "twitter"
        assert utm["utm_campaign"] == "launch"
        assert "other" not in utm

    def test_extract_utm_from_url_without_params(self):
        """Should handle URLs without UTM params."""
        url = "https://example.com/path?query=value"
        clean_url, utm = extract_utm_from_url(url)

        assert clean_url == url
        assert utm == {}

    def test_merge_utm_params_cli_precedence(self):
        """CLI params should override URL params."""
        url_params = {"utm_source": "url_source", "utm_medium": "url_medium"}
        cli_params = {"utm_source": "cli_source", "utm_campaign": "cli_campaign"}

        result = merge_utm_params(url_params, cli_params)

        assert result["utm_source"] == "cli_source"  # CLI wins
        assert result["utm_medium"] == "url_medium"  # Preserved from URL
        assert result["utm_campaign"] == "cli_campaign"  # Added from CLI


class TestCreateLinkRequest:
    """Tests for CreateLinkRequest model."""

    def test_to_api_dict_excludes_none(self):
        """Should exclude None values from API dict."""
        request = CreateLinkRequest(
            url="https://example.com",
            key="test",
            domain=None,
            utm_source="twitter",
        )
        api_dict = request.to_api_dict()

        assert api_dict["url"] == "https://example.com"
        assert api_dict["key"] == "test"
        assert api_dict["utm_source"] == "twitter"
        assert "domain" not in api_dict


class TestAddCommand:
    """Tests for the add command."""

    @patch("dubco_cli.commands.add.DubClient")
    @patch("dubco_cli.config.get_client_id")
    @patch("dubco_cli.config.load_credentials")
    def test_add_single_link(
        self, mock_creds, mock_client_id, mock_client_cls, sample_link_response
    ):
        """Should create a single link successfully."""
        mock_client_id.return_value = "test_client_id"
        mock_creds.return_value = MagicMock(
            access_token="test_token",
            expires_at=9999999999,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        mock_client.post.return_value = sample_link_response

        result = runner.invoke(app, ["add", "https://example.com", "-k", "test-link"])

        assert result.exit_code == 0
        assert "Created" in result.output

    def test_add_dry_run(self):
        """Should show what would be created in dry-run mode."""
        result = runner.invoke(
            app,
            ["add", "https://example.com", "-k", "test", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "https://example.com" in result.output

    def test_add_requires_url_or_file(self):
        """Should error when neither URL nor file is provided."""
        result = runner.invoke(app, ["add"])

        assert result.exit_code == 2
        assert "Error" in result.output
