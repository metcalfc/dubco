"""Link detail panel widget."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label, Static

from dubco_cli.models.link import Link


class LinkDetailPanel(Static):
    """Panel showing details of the selected link."""

    DEFAULT_CSS = """
    LinkDetailPanel {
        height: auto;
        max-height: 12;
        border-top: solid $primary;
        padding: 1;
        background: $surface;
    }

    LinkDetailPanel .detail-row {
        height: auto;
        margin-bottom: 1;
    }

    LinkDetailPanel .detail-label {
        width: 12;
        color: $text-muted;
    }

    LinkDetailPanel .detail-value {
        width: 1fr;
    }

    LinkDetailPanel .stats-container {
        height: 3;
    }

    LinkDetailPanel .stat-box {
        width: 1fr;
        height: 3;
        border: solid $primary;
        padding: 0 1;
        margin-right: 1;
        content-align: center middle;
    }

    LinkDetailPanel .stat-value {
        text-style: bold;
    }

    LinkDetailPanel .stat-label {
        color: $text-muted;
    }

    LinkDetailPanel.hidden {
        display: none;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._link: Link | None = None

    def compose(self) -> ComposeResult:
        with Vertical():
            # URL row
            with Horizontal(classes="detail-row"):
                yield Label("URL:", classes="detail-label")
                yield Label("", id="detail-url", classes="detail-value")

            # Tags and Created row
            with Horizontal(classes="detail-row"):
                yield Label("Tags:", classes="detail-label")
                yield Label("", id="detail-tags", classes="detail-value")

            # UTM row
            with Horizontal(classes="detail-row"):
                yield Label("UTM:", classes="detail-label")
                yield Label("", id="detail-utm", classes="detail-value")

            # Stats row
            with Horizontal(classes="stats-container"):
                with Container(classes="stat-box"):
                    yield Label("0", id="stat-clicks", classes="stat-value")
                    yield Label("clicks", classes="stat-label")
                with Container(classes="stat-box"):
                    yield Label("0", id="stat-leads", classes="stat-value")
                    yield Label("leads", classes="stat-label")

    def update_link(self, link: Link | None) -> None:
        """Update the panel with link details."""
        self._link = link

        if link is None:
            self.add_class("hidden")
            return

        self.remove_class("hidden")

        # Update URL
        url_label = self.query_one("#detail-url", Label)
        url_label.update(link.url)

        # Update tags
        tags_label = self.query_one("#detail-tags", Label)
        tags = ", ".join(link.tag_names) if link.tag_names else "None"
        tags_label.update(tags)

        # Update UTM
        utm_label = self.query_one("#detail-utm", Label)
        utm_parts = []
        if link.utm_source:
            utm_parts.append(f"source={link.utm_source}")
        if link.utm_medium:
            utm_parts.append(f"medium={link.utm_medium}")
        if link.utm_campaign:
            utm_parts.append(f"campaign={link.utm_campaign}")
        utm_label.update(", ".join(utm_parts) if utm_parts else "None")

        # Update stats
        clicks_label = self.query_one("#stat-clicks", Label)
        clicks_label.update(f"{link.clicks:,}")

        leads_label = self.query_one("#stat-leads", Label)
        leads_label.update(f"{link.leads:,}")

    def show(self) -> None:
        """Show the panel."""
        self.remove_class("hidden")

    def hide(self) -> None:
        """Hide the panel."""
        self.add_class("hidden")

    def toggle(self) -> None:
        """Toggle panel visibility."""
        if self.has_class("hidden"):
            self.show()
        else:
            self.hide()
