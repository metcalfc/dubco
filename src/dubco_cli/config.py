"""Configuration and credential storage for dubco-cli."""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    if xdg_config := os.environ.get("XDG_CONFIG_HOME"):
        config_dir = Path(xdg_config) / "dubco"
    else:
        config_dir = Path.home() / ".config" / "dubco"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_credentials_path() -> Path:
    """Get the credentials file path."""
    return get_config_dir() / "credentials.json"


def get_config_path() -> Path:
    """Get the config file path (for client_id, etc.)."""
    return get_config_dir() / "config.json"


class Credentials(BaseModel):
    """OAuth credentials storage."""

    access_token: str
    refresh_token: str
    expires_at: int
    workspace_id: str
    workspace_name: str


class Config(BaseModel):
    """CLI configuration storage."""

    client_id: str


def load_credentials() -> Credentials | None:
    """Load credentials from disk."""
    path = get_credentials_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return Credentials(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def save_credentials(credentials: Credentials) -> None:
    """Save credentials to disk."""
    path = get_credentials_path()
    path.write_text(credentials.model_dump_json(indent=2))
    path.chmod(0o600)  # Restrict permissions


def clear_credentials() -> None:
    """Remove stored credentials."""
    path = get_credentials_path()
    if path.exists():
        path.unlink()


def load_config() -> Config | None:
    """Load config from disk."""
    path = get_config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return Config(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def save_config(config: Config) -> None:
    """Save config to disk."""
    path = get_config_path()
    path.write_text(config.model_dump_json(indent=2))


def get_client_id() -> str | None:
    """Get the stored client_id."""
    config = load_config()
    return config.client_id if config else None


def set_client_id(client_id: str) -> None:
    """Store the client_id."""
    save_config(Config(client_id=client_id))
