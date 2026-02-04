"""Main TUI application."""

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from dubco_cli.api.client import DubClient
from dubco_cli.tui.screens.main import MainScreen
from dubco_cli.tui.state import AppState


class DubTUIApp(App):
    """Dub.co Link Manager TUI Application."""

    TITLE = "Dub.co Link Manager"
    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "help", "Help", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.client = DubClient()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.push_screen(MainScreen())

    def action_help(self) -> None:
        """Show help screen."""
        self.notify(
            "Keys: j/k=navigate, p=preview, e=edit, d=delete, /=search, Tab=switch pane",
            title="Help",
            timeout=5,
        )

    def action_refresh(self) -> None:
        """Refresh the current screen."""
        screen = self.screen
        if hasattr(screen, "refresh_data"):
            screen.refresh_data()

    def on_unmount(self) -> None:
        """Called when app is unmounted."""
        self.client.close()
