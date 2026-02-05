"""Tests for the rm command."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dubco_cli.main import app

runner = CliRunner()


class TestRmCommand:
    """Tests for the rm command."""

    def test_rm_requires_identifier(self):
        """Should error when no link identifier is provided."""
        result = runner.invoke(app, ["rm"])

        assert result.exit_code == 2
        assert "No links specified" in result.output

    @patch("dubco_cli.commands.rm.DubClient")
    @patch("dubco_cli.commands.rm.get_link")
    @patch("dubco_cli.config.get_client_id")
    @patch("dubco_cli.config.load_credentials")
    def test_rm_not_found(self, mock_creds, mock_client_id, mock_get_link, mock_client_cls):
        """Should error when link is not found."""
        mock_client_id.return_value = "test_client_id"
        mock_creds.return_value = MagicMock(
            access_token="test_token",
            expires_at=9999999999,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        mock_get_link.return_value = None

        result = runner.invoke(app, ["rm", "nonexistent-link", "-d", "dub.sh"])

        assert result.exit_code == 4
        assert "not found" in result.output.lower()

    @patch("dubco_cli.commands.rm.DubClient")
    @patch("dubco_cli.commands.rm.get_link")
    @patch("dubco_cli.commands.rm.delete_link")
    @patch("dubco_cli.config.get_client_id")
    @patch("dubco_cli.config.load_credentials")
    def test_rm_with_force(
        self,
        mock_creds,
        mock_client_id,
        mock_delete,
        mock_get_link,
        mock_client_cls,
        sample_link_response,
    ):
        """Should delete without confirmation when --force is used."""
        mock_client_id.return_value = "test_client_id"
        mock_creds.return_value = MagicMock(
            access_token="test_token",
            expires_at=9999999999,
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from dubco_cli.models.link import Link

        mock_get_link.return_value = Link(**sample_link_response)
        mock_delete.return_value = True

        result = runner.invoke(app, ["rm", "test-link", "-d", "dub.sh", "--force"])

        assert result.exit_code == 0
        assert "Deleted" in result.output
        mock_delete.assert_called_once()
