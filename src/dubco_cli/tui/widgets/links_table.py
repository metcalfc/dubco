"""Links table widget."""

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Static

from dubco_cli.models.link import Link


class LinkSelected(Message):
    """Message sent when a link is selected."""

    def __init__(self, link: Link | None) -> None:
        self.link = link
        super().__init__()


class LinksTable(Static):
    """Table displaying links."""

    DEFAULT_CSS = """
    LinksTable {
        height: 100%;
        width: 100%;
    }

    LinksTable DataTable {
        height: 100%;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._links: list[Link] = []
        self._link_map: dict[str, Link] = {}

    def compose(self) -> ComposeResult:
        table = DataTable(id="links-table", cursor_type="row")
        yield table

    def on_mount(self) -> None:
        """Set up table columns."""
        table = self.query_one("#links-table", DataTable)
        table.add_columns(
            "Short Link",
            "Destination",
            "Tags",
            "Clicks",
            "Created",
        )

    def update_links(self, links: list[Link]) -> None:
        """Update the table with new links."""
        self._links = links
        self._link_map = {link.id: link for link in links}

        table = self.query_one("#links-table", DataTable)
        table.clear()

        for link in links:
            # Truncate destination URL
            dest = link.url
            if len(dest) > 40:
                dest = dest[:37] + "..."

            # Format tags
            tags = ", ".join(link.tag_names[:2])
            if len(link.tag_names) > 2:
                tags += f" +{len(link.tag_names) - 2}"

            # Format clicks
            clicks = f"{link.clicks:,}"

            # Format created date
            created = self._format_relative_time(link.created)

            table.add_row(
                link.shortLink,
                dest,
                tags,
                clicks,
                created,
                key=link.id,
            )

        # Select first row if available
        if links:
            table.move_cursor(row=0)
            self.post_message(LinkSelected(links[0]))

    def _format_relative_time(self, dt: datetime) -> str:
        """Format datetime as relative time."""
        now = datetime.now(timezone.utc)
        diff = now - dt

        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"

    def get_selected_link(self) -> Link | None:
        """Get the currently selected link."""
        table = self.query_one("#links-table", DataTable)
        if table.cursor_row is not None and table.row_count > 0:
            try:
                # The row key is stored when we add the row
                cell_key = table.coordinate_to_cell_key((table.cursor_row, 0))
                link_id = cell_key.row_key.value
                return self._link_map.get(link_id)
            except Exception:
                pass
        return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if event.row_key:
            link = self._link_map.get(event.row_key.value)
            self.post_message(LinkSelected(link))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor move)."""
        if event.row_key:
            link = self._link_map.get(event.row_key.value)
            self.post_message(LinkSelected(link))
