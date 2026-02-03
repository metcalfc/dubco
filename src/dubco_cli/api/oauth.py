"""OAuth PKCE flow implementation for Dub.co."""

import base64
import hashlib
import http.server
import secrets
import socketserver
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from rich.console import Console

from dubco_cli.config import Credentials, load_credentials, save_credentials

console = Console()

# Dub.co OAuth endpoints
AUTHORIZE_URL = "https://app.dub.co/oauth/authorize"
TOKEN_URL = "https://api.dub.co/oauth/token"
USERINFO_URL = "https://api.dub.co/oauth/userinfo"

# Scopes needed for the CLI
SCOPES = ["links.read", "links.write", "tags.read", "user.read"]

# Token lifetime (2 hours in seconds, refresh 5 minutes before expiry)
TOKEN_REFRESH_BUFFER = 300


def generate_code_verifier() -> str:
    """Generate a random code verifier (43-128 chars)."""
    return secrets.token_urlsafe(64)[:96]


def generate_code_challenge(verifier: str) -> str:
    """Generate SHA256 code challenge from verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def generate_state() -> str:
    """Generate a random state parameter."""
    return secrets.token_urlsafe(32)


@dataclass
class OAuthCallback:
    """Stores the OAuth callback result."""

    code: str | None = None
    state: str | None = None
    error: str | None = None
    received: threading.Event = field(default_factory=threading.Event)


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    callback_data: OAuthCallback

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle the OAuth callback GET request."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/callback":
            if "error" in params:
                self.callback_data.error = params["error"][0]
            elif "code" in params:
                self.callback_data.code = params["code"][0]
                self.callback_data.state = params.get("state", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if self.callback_data.error:
                html = """
                <html><body style="font-family: system-ui; text-align: center; padding: 50px;">
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window.</p>
                </body></html>
                """.format(error=self.callback_data.error)
            else:
                html = """
                <html><body style="font-family: system-ui; text-align: center; padding: 50px;">
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
                """
            self.wfile.write(html.encode())
            self.callback_data.received.set()
        else:
            self.send_error(404)


class OAuthFlow:
    """Handles the OAuth PKCE flow for Dub.co."""

    def __init__(self, client_id: str, port: int = 8484):
        self.client_id = client_id
        self.port = port
        self.redirect_uri = f"http://localhost:{port}/callback"

    def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """Build the authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> dict:
        """Exchange authorization code for access tokens."""
        with httpx.Client() as client:
            response = client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "code_verifier": code_verifier,
                },
            )
            response.raise_for_status()
            return response.json()

    def refresh_tokens(self, refresh_token: str) -> dict:
        """Refresh the access token."""
        with httpx.Client() as client:
            response = client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()

    def get_user_info(self, access_token: str) -> dict:
        """Get user/workspace info from the token."""
        with httpx.Client() as client:
            response = client.get(
                USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def run_login_flow(self) -> Credentials:
        """Run the complete OAuth PKCE login flow."""
        # Generate PKCE values
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()

        # Set up callback handler
        callback_data = OAuthCallback()
        OAuthCallbackHandler.callback_data = callback_data

        # Start local server
        with socketserver.TCPServer(("", self.port), OAuthCallbackHandler) as server:
            server_thread = threading.Thread(target=server.handle_request)
            server_thread.start()

            # Open browser
            auth_url = self.get_authorization_url(state, code_challenge)
            console.print(f"\nOpening browser for authentication...")
            console.print(f"If browser doesn't open, visit: {auth_url}\n")
            webbrowser.open(auth_url)

            # Wait for callback
            if not callback_data.received.wait(timeout=120):
                raise TimeoutError("Authentication timed out after 2 minutes")

            server_thread.join(timeout=1)

        # Check for errors
        if callback_data.error:
            raise RuntimeError(f"Authentication failed: {callback_data.error}")

        if callback_data.state != state:
            raise RuntimeError("State mismatch - possible CSRF attack")

        # Exchange code for tokens
        console.print("Exchanging code for tokens...")
        token_data = self.exchange_code_for_tokens(callback_data.code, code_verifier)

        # Get workspace info
        user_info = self.get_user_info(token_data["access_token"])

        # Build credentials
        credentials = Credentials(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_at=int(time.time()) + token_data.get("expires_in", 7200),
            workspace_id=user_info.get("workspace", {}).get("id", ""),
            workspace_name=user_info.get("workspace", {}).get("name", ""),
        )

        # Save credentials
        save_credentials(credentials)

        return credentials


def ensure_valid_token(client_id: str) -> Credentials:
    """Ensure we have a valid (non-expired) access token.

    Returns the current credentials or refreshes them if expired.
    """
    credentials = load_credentials()
    if not credentials:
        raise RuntimeError("Not logged in. Run 'dub login' first.")

    # Check if token is about to expire
    if time.time() >= credentials.expires_at - TOKEN_REFRESH_BUFFER:
        console.print("[dim]Refreshing access token...[/dim]")
        flow = OAuthFlow(client_id)
        try:
            token_data = flow.refresh_tokens(credentials.refresh_token)
            user_info = flow.get_user_info(token_data["access_token"])

            credentials = Credentials(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=int(time.time()) + token_data.get("expires_in", 7200),
                workspace_id=user_info.get("workspace", {}).get("id", credentials.workspace_id),
                workspace_name=user_info.get("workspace", {}).get("name", credentials.workspace_name),
            )
            save_credentials(credentials)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError(
                    "Session expired. Please run 'dub login' again."
                ) from e
            raise

    return credentials
