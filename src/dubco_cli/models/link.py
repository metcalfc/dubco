"""Link models for Dub.co API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateLinkRequest(BaseModel):
    """Request model for creating a link."""

    url: str = Field(..., description="The destination URL")
    domain: str | None = Field(None, description="The short link domain")
    key: str | None = Field(None, description="The short link slug")
    externalId: str | None = Field(None, description="External ID for reference")
    prefix: str | None = Field(None, description="Prefix for generated key")
    trackConversion: bool | None = Field(None, description="Track conversions")
    archived: bool | None = Field(None, description="Whether link is archived")
    publicStats: bool | None = Field(None, description="Public stats page")
    tagIds: list[str] | None = Field(None, description="Tag IDs to associate")
    tagNames: list[str] | None = Field(None, description="Tag names to associate")
    comments: str | None = Field(None, description="Comments for the link")
    expiresAt: str | None = Field(None, description="Expiration date")
    expiredUrl: str | None = Field(None, description="URL to redirect when expired")
    password: str | None = Field(None, description="Password protection")
    proxy: bool | None = Field(None, description="Enable link cloaking")
    title: str | None = Field(None, description="Custom OG title")
    description: str | None = Field(None, description="Custom OG description")
    image: str | None = Field(None, description="Custom OG image")
    video: str | None = Field(None, description="Custom OG video")
    rewrite: bool | None = Field(None, description="Enable link rewriting")
    ios: str | None = Field(None, description="iOS-specific redirect")
    android: str | None = Field(None, description="Android-specific redirect")
    geo: dict[str, str] | None = Field(None, description="Geo-targeting")
    doIndex: bool | None = Field(None, description="Allow search indexing")
    utm_source: str | None = Field(None, description="UTM source")
    utm_medium: str | None = Field(None, description="UTM medium")
    utm_campaign: str | None = Field(None, description="UTM campaign")
    utm_term: str | None = Field(None, description="UTM term")
    utm_content: str | None = Field(None, description="UTM content")

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to dict for API, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class UpdateLinkRequest(BaseModel):
    """Request model for updating a link."""

    url: str | None = Field(None, description="The destination URL")
    domain: str | None = Field(None, description="The short link domain")
    key: str | None = Field(None, description="The short link slug")
    externalId: str | None = Field(None, description="External ID for reference")
    trackConversion: bool | None = Field(None, description="Track conversions")
    archived: bool | None = Field(None, description="Whether link is archived")
    publicStats: bool | None = Field(None, description="Public stats page")
    tagIds: list[str] | None = Field(None, description="Tag IDs to associate")
    tagNames: list[str] | None = Field(None, description="Tag names to associate")
    comments: str | None = Field(None, description="Comments for the link")
    expiresAt: str | None = Field(None, description="Expiration date")
    expiredUrl: str | None = Field(None, description="URL to redirect when expired")
    password: str | None = Field(None, description="Password protection")
    proxy: bool | None = Field(None, description="Enable link cloaking")
    title: str | None = Field(None, description="Custom OG title")
    description: str | None = Field(None, description="Custom OG description")
    image: str | None = Field(None, description="Custom OG image")
    video: str | None = Field(None, description="Custom OG video")
    rewrite: bool | None = Field(None, description="Enable link rewriting")
    ios: str | None = Field(None, description="iOS-specific redirect")
    android: str | None = Field(None, description="Android-specific redirect")
    geo: dict[str, str] | None = Field(None, description="Geo-targeting")
    doIndex: bool | None = Field(None, description="Allow search indexing")
    utm_source: str | None = Field(None, description="UTM source")
    utm_medium: str | None = Field(None, description="UTM medium")
    utm_campaign: str | None = Field(None, description="UTM campaign")
    utm_term: str | None = Field(None, description="UTM term")
    utm_content: str | None = Field(None, description="UTM content")

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to dict for API, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class Link(BaseModel):
    """Model for a Dub.co link."""

    id: str
    domain: str
    key: str
    url: str
    shortLink: str
    archived: bool = False
    expiresAt: str | None = None
    expiredUrl: str | None = None
    password: str | None = None
    proxy: bool = False
    title: str | None = None
    description: str | None = None
    image: str | None = None
    video: str | None = None
    rewrite: bool = False
    doIndex: bool = False
    ios: str | None = None
    android: str | None = None
    geo: dict[str, str] | None = None
    publicStats: bool = False
    tagId: str | None = None
    tags: list[dict[str, Any]] | None = None
    comments: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    userId: str
    workspaceId: str
    clicks: int = 0
    lastClicked: str | None = None
    leads: int = 0
    sales: int = 0
    saleAmount: int = 0
    createdAt: str
    updatedAt: str
    projectId: str | None = None  # Deprecated, alias for workspaceId
    externalId: str | None = None
    trackConversion: bool = False

    @property
    def short_url(self) -> str:
        """Get the short URL."""
        return self.shortLink

    @property
    def created(self) -> datetime:
        """Get created datetime."""
        return datetime.fromisoformat(self.createdAt.replace("Z", "+00:00"))

    @property
    def tag_names(self) -> list[str]:
        """Get list of tag names."""
        if not self.tags:
            return []
        return [t.get("name", "") for t in self.tags if t.get("name")]


class BulkCreateResult(BaseModel):
    """Result of bulk link creation."""

    created: list[Link] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
