"""Authentication models for Dub.co API."""

from pydantic import BaseModel


class UserInfo(BaseModel):
    """User information from OAuth."""

    id: str
    name: str | None = None
    email: str | None = None
    image: str | None = None


class WorkspaceInfo(BaseModel):
    """Workspace information from OAuth."""

    id: str
    name: str
    slug: str
    logo: str | None = None


class TokenResponse(BaseModel):
    """OAuth token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 7200
    scope: str | None = None
