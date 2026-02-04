"""State management for the TUI."""

from dataclasses import dataclass, field
from enum import Enum

from dubco_cli.models.link import Link


class FilterType(Enum):
    """Type of filter applied to links."""

    ALL = "all"
    TAG = "tag"
    DOMAIN = "domain"
    ARCHIVED = "archived"


@dataclass
class FilterState:
    """Current filter state for link listing."""

    filter_type: FilterType = FilterType.ALL
    tag_name: str | None = None
    domain: str | None = None
    search: str | None = None

    def clear(self) -> None:
        """Reset to default state."""
        self.filter_type = FilterType.ALL
        self.tag_name = None
        self.domain = None
        self.search = None


@dataclass
class AppState:
    """Application state container."""

    links: list[Link] = field(default_factory=list)
    selected_link: Link | None = None
    filter_state: FilterState = field(default_factory=FilterState)
    tags: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    loading: bool = False
    error: str | None = None
    show_detail_panel: bool = False

    def get_unique_tags(self) -> list[str]:
        """Extract unique tags from loaded links."""
        tags = set()
        for link in self.links:
            for tag in link.tag_names:
                tags.add(tag)
        return sorted(tags)

    def get_unique_domains(self) -> list[str]:
        """Extract unique domains from loaded links."""
        domains = set()
        for link in self.links:
            domains.add(link.domain)
        return sorted(domains)

    def refresh_metadata(self) -> None:
        """Refresh tags and domains from current links."""
        self.tags = self.get_unique_tags()
        self.domains = self.get_unique_domains()
