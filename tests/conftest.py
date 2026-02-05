"""Pytest configuration and fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def mock_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "dubco"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_credentials(mock_config_dir):
    """Create mock credentials file."""
    creds = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,  # Far future
        "workspace_id": "ws_test123",
        "workspace_name": "Test Workspace",
    }
    creds_path = mock_config_dir / "credentials.json"
    creds_path.write_text(json.dumps(creds))
    return creds_path


@pytest.fixture
def mock_config(mock_config_dir):
    """Create mock config file with client_id."""
    config = {"client_id": "dub_app_test123"}
    config_path = mock_config_dir / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


@pytest.fixture
def configured_env(mock_config_dir, mock_credentials, mock_config, monkeypatch):
    """Set up a fully configured environment."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(mock_config_dir.parent))
    return mock_config_dir


@pytest.fixture
def sample_link_response():
    """Sample API response for a single link."""
    return {
        "id": "clx1234567890",
        "domain": "dub.sh",
        "key": "test-link",
        "url": "https://example.com",
        "shortLink": "https://dub.sh/test-link",
        "archived": False,
        "proxy": False,
        "rewrite": False,
        "doIndex": False,
        "publicStats": False,
        "userId": "user_123",
        "workspaceId": "ws_123",
        "clicks": 42,
        "leads": 0,
        "sales": 0,
        "saleAmount": 0,
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z",
        "trackConversion": False,
    }


@pytest.fixture
def sample_links_response(sample_link_response):
    """Sample API response for list of links."""
    return [
        sample_link_response,
        {
            **sample_link_response,
            "id": "clx0987654321",
            "key": "another-link",
            "shortLink": "https://dub.sh/another-link",
            "url": "https://example.org",
            "clicks": 10,
        },
    ]


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for bulk operations."""
    return """url,key,domain,tag
https://example.com/page1,page1,dub.sh,marketing
https://example.com/page2,page2,dub.sh,sales
https://example.com/page3,page3,dub.sh,marketing
"""


# VCR.py configuration for recording API responses
@pytest.fixture(scope="module")
def vcr_config():
    """VCR.py configuration."""
    return {
        "filter_headers": ["authorization"],
        "record_mode": "none",  # Change to "new_episodes" to record new cassettes
        "cassette_library_dir": str(Path(__file__).parent / "cassettes"),
    }
