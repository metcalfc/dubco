"""Delete confirmation modal."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from dubco_cli.models.link import Link


class ConfirmDeleteModal(ModalScreen):
    """Modal for confirming link deletion."""

    DEFAULT_CSS = """
    ConfirmDeleteModal {
        align: center middle;
    }

    ConfirmDeleteModal > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $error;
        padding: 1 2;
    }

    ConfirmDeleteModal .title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    ConfirmDeleteModal .message {
        margin-bottom: 1;
    }

    ConfirmDeleteModal .warning {
        color: $warning;
        margin-bottom: 1;
    }

    ConfirmDeleteModal .buttons {
        height: 3;
        margin-top: 1;
        align: right middle;
    }

    ConfirmDeleteModal Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, link: Link, **kwargs) -> None:
        super().__init__(**kwargs)
        self._link = link

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Delete Link", classes="title")
            yield Label(
                f"Are you sure you want to delete '{self._link.shortLink}'?",
                classes="message",
            )

            if self._link.clicks > 0:
                yield Label(
                    f"Warning: This link has {self._link.clicks:,} clicks!",
                    classes="warning",
                )

            with Horizontal(classes="buttons"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Delete", variant="error", id="delete-btn")

    def action_cancel(self) -> None:
        """Cancel deletion."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "delete-btn":
            self.dismiss(True)
