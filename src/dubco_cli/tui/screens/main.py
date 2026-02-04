"""Main screen with sidebar and links table."""

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Input, Static

from dubco_cli.api.client import DubAPIError
from dubco_cli.api.links import delete_link, list_all_links, update_link
from dubco_cli.models.link import Link, UpdateLinkRequest
from dubco_cli.tui.screens.detail import LinkDetailPanel
from dubco_cli.tui.screens.modals.delete import ConfirmDeleteModal
from dubco_cli.tui.screens.modals.edit import LinkEditModal
from dubco_cli.tui.state import FilterState, FilterType
from dubco_cli.tui.widgets.footer import Footer
from dubco_cli.tui.widgets.links_table import LinkSelected, LinksTable
from dubco_cli.tui.widgets.sidebar import FilterChanged, Sidebar


class MainScreen(Screen):
    """Main screen with sidebar and links table."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("p", "toggle_preview", "Preview", show=True),
        Binding("e", "edit_link", "Edit", show=True),
        Binding("d", "delete_link", "Delete", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("tab", "focus_next", "Switch", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1;
    }

    #main-container {
        layout: horizontal;
        height: 100%;
    }

    #content-area {
        width: 1fr;
        height: 100%;
    }

    #table-container {
        height: 1fr;
    }

    #search-container {
        height: 3;
        display: none;
        padding: 0 1;
    }

    #search-container.visible {
        display: block;
    }

    #search-input {
        width: 100%;
    }

    #loading-indicator {
        width: 100%;
        height: 100%;
        content-align: center middle;
        display: none;
    }

    #loading-indicator.loading {
        display: block;
    }

    #error-message {
        width: 100%;
        padding: 1;
        background: $error;
        color: $text;
        display: none;
    }

    #error-message.visible {
        display: block;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._selected_link: Link | None = None
        self._filter_state = FilterState()

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            yield Sidebar(id="sidebar")

            with Vertical(id="content-area"):
                # Search bar (hidden by default)
                with Container(id="search-container"):
                    yield Input(placeholder="Search links...", id="search-input")

                # Error message
                yield Static("", id="error-message")

                # Loading indicator
                yield Static("Loading...", id="loading-indicator")

                # Table container
                with Container(id="table-container"):
                    yield LinksTable(id="links-table")

                # Detail panel (hidden by default)
                yield LinkDetailPanel(id="detail-panel", classes="hidden")

        yield Footer()

    def on_mount(self) -> None:
        """Load initial data."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh link data from API."""
        self._show_loading(True)
        self._hide_error()
        self.load_links()

    @property
    def state(self):
        """Get app state."""
        return self.app.state

    @property
    def client(self):
        """Get API client."""
        return self.app.client

    def load_links(self) -> None:
        """Load links in a worker thread."""
        self._fetch_links()

    @work(thread=True, exclusive=True)
    def _fetch_links(self) -> None:
        """Fetch links from API in a background thread."""
        try:
            # Build filter params
            domain = None
            tag_names = None
            search = self._filter_state.search

            if self._filter_state.filter_type == FilterType.DOMAIN:
                domain = self._filter_state.domain
            elif self._filter_state.filter_type == FilterType.TAG:
                tag_names = [self._filter_state.tag_name] if self._filter_state.tag_name else None

            # Fetch links
            links = list_all_links(
                self.client,
                domain=domain,
                tag_names=tag_names,
                search=search,
                limit=500,
            )

            # Filter archived if needed
            if self._filter_state.filter_type == FilterType.ARCHIVED:
                links = [link for link in links if link.archived]
            elif self._filter_state.filter_type != FilterType.ARCHIVED:
                # By default, don't show archived
                links = [link for link in links if not link.archived]

            self.app.call_from_thread(self._on_links_loaded, links)

        except DubAPIError as e:
            self.app.call_from_thread(self._on_load_error, str(e))

    def _on_links_loaded(self, links: list[Link]) -> None:
        """Handle loaded links."""
        self._show_loading(False)
        self.state.links = links
        self.state.refresh_metadata()

        # Update sidebar with tags and domains
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.update_metadata(self.state.tags, self.state.domains)

        # Update table
        table = self.query_one("#links-table", LinksTable)
        table.update_links(links)

    def _on_load_error(self, error: str) -> None:
        """Handle load error."""
        self._show_loading(False)
        self._show_error(error)

    def _show_loading(self, show: bool) -> None:
        """Show/hide loading indicator."""
        indicator = self.query_one("#loading-indicator", Static)
        if show:
            indicator.add_class("loading")
        else:
            indicator.remove_class("loading")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        error = self.query_one("#error-message", Static)
        error.update(f"Error: {message}")
        error.add_class("visible")

    def _hide_error(self) -> None:
        """Hide error message."""
        error = self.query_one("#error-message", Static)
        error.remove_class("visible")

    def on_filter_changed(self, event: FilterChanged) -> None:
        """Handle filter change from sidebar."""
        self._filter_state = event.filter_state
        self.refresh_data()

    def on_link_selected(self, event: LinkSelected) -> None:
        """Handle link selection from table."""
        self._selected_link = event.link
        detail_panel = self.query_one("#detail-panel", LinkDetailPanel)
        detail_panel.update_link(event.link)

    def action_cursor_down(self) -> None:
        """Move cursor down in table."""
        table = self.query_one("#links-table LinksTable DataTable")
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in table."""
        table = self.query_one("#links-table LinksTable DataTable")
        table.action_cursor_up()

    def action_toggle_preview(self) -> None:
        """Toggle detail panel visibility."""
        detail_panel = self.query_one("#detail-panel", LinkDetailPanel)
        detail_panel.toggle()

    def action_edit_link(self) -> None:
        """Edit the selected link."""
        if self._selected_link:
            self.app.push_screen(
                LinkEditModal(self._selected_link),
                self._on_edit_complete,
            )

    def _on_edit_complete(self, result: UpdateLinkRequest | None) -> None:
        """Handle edit modal result."""
        if result is None or self._selected_link is None:
            return

        # Check if any changes were made
        if not result.to_api_dict():
            self.notify("No changes made")
            return

        try:
            updated_link = update_link(self.client, self._selected_link.id, result)
            self.notify(f"Updated {updated_link.shortLink}")
            self.refresh_data()
        except DubAPIError as e:
            self.notify(f"Error: {e}", severity="error")

    def action_delete_link(self) -> None:
        """Delete the selected link."""
        if self._selected_link:
            self.app.push_screen(
                ConfirmDeleteModal(self._selected_link),
                self._on_delete_confirm,
            )

    def _on_delete_confirm(self, confirmed: bool) -> None:
        """Handle delete confirmation."""
        if not confirmed or self._selected_link is None:
            return

        try:
            delete_link(self.client, self._selected_link.id)
            self.notify(f"Deleted {self._selected_link.shortLink}")
            self._selected_link = None
            self.refresh_data()
        except DubAPIError as e:
            self.notify(f"Error: {e}", severity="error")

    def action_search(self) -> None:
        """Show search input."""
        search_container = self.query_one("#search-container", Container)
        search_container.add_class("visible")
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear and hide search."""
        search_container = self.query_one("#search-container", Container)
        search_container.remove_class("visible")
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self._filter_state.search = None
        self.refresh_data()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "search-input":
            self._filter_state.search = event.value if event.value else None
            self.refresh_data()
