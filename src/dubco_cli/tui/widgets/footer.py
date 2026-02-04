"""Footer widget showing keybindings."""

from textual.app import ComposeResult
from textual.widgets import Static


class Footer(Static):
    """Footer showing available keybindings."""

    DEFAULT_CSS = """
    Footer {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._bindings = [
            ("j/k", "Navigate"),
            ("p", "Preview"),
            ("e", "Edit"),
            ("d", "Delete"),
            ("/", "Search"),
            ("r", "Refresh"),
            ("Tab", "Switch"),
            ("q", "Quit"),
        ]

    def compose(self) -> ComposeResult:
        text = "  ".join(f"[bold]{key}[/bold] {action}" for key, action in self._bindings)
        yield Static(text, markup=True)
