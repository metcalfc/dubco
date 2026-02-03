"""HTTP client for Dub.co API."""

import time
from typing import Any

import httpx
from rich.console import Console

from dubco_cli.api.oauth import ensure_valid_token
from dubco_cli.config import get_client_id, load_credentials

console = Console()

API_BASE_URL = "https://api.dub.co"

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # Exponential backoff in seconds


class DubAPIError(Exception):
    """Exception for Dub.co API errors."""

    def __init__(self, message: str, status_code: int = 0, error_code: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class DubClient:
    """HTTP client for Dub.co API with automatic token refresh."""

    def __init__(self):
        self._client: httpx.Client | None = None
        self._access_token: str | None = None

    def _ensure_authenticated(self) -> str:
        """Ensure we have a valid access token."""
        client_id = get_client_id()
        if not client_id:
            raise DubAPIError("Not configured. Run 'dub login' first.", status_code=401)

        credentials = ensure_valid_token(client_id)
        return credentials.access_token

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        token = self._ensure_authenticated()

        # Recreate client if token changed
        if self._client is None or self._access_token != token:
            if self._client:
                self._client.close()
            self._access_token = token
            self._client = httpx.Client(
                base_url=API_BASE_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate errors."""
        if response.status_code == 429:
            # Rate limited - let caller handle retry
            raise DubAPIError(
                "Rate limited",
                status_code=429,
                error_code="rate_limited",
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("error", {}).get("message", response.text)
                code = error_data.get("error", {}).get("code", "")
            except (ValueError, KeyError):
                message = response.text
                code = ""

            raise DubAPIError(message, status_code=response.status_code, error_code=code)

        if response.status_code == 204:
            return {}

        return response.json()

    def _request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> dict[str, Any]:
        """Make a request with automatic retry on rate limits."""
        client = self._get_client()

        for attempt in range(MAX_RETRIES):
            try:
                response = client.request(method, url, **kwargs)
                return self._handle_response(response)
            except DubAPIError as e:
                if e.status_code == 429 and attempt < MAX_RETRIES - 1:
                    sleep_time = RETRY_BACKOFF[attempt]
                    console.print(f"[yellow]Rate limited, retrying in {sleep_time}s...[/yellow]")
                    time.sleep(sleep_time)
                    continue
                raise

        raise DubAPIError("Max retries exceeded")

    def get(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """Make a GET request."""
        return self._request_with_retry("GET", url, params=params)

    def post(self, url: str, json: dict | None = None) -> dict[str, Any]:
        """Make a POST request."""
        return self._request_with_retry("POST", url, json=json)

    def delete(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """Make a DELETE request."""
        return self._request_with_retry("DELETE", url, params=params)

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
