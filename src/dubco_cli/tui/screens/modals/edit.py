"""Link edit modal."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from dubco_cli.models.link import Link, UpdateLinkRequest


class LinkUpdated(Message):
    """Message sent when a link is updated."""

    def __init__(self, link: Link) -> None:
        self.link = link
        super().__init__()


class LinkEditModal(ModalScreen):
    """Modal for editing a link."""

    DEFAULT_CSS = """
    LinkEditModal {
        align: center middle;
    }

    LinkEditModal > Vertical {
        width: 80;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    LinkEditModal .title {
        text-style: bold;
        margin-bottom: 1;
    }

    LinkEditModal .form-row {
        height: auto;
        margin-bottom: 1;
    }

    LinkEditModal .form-label {
        width: 15;
        padding-top: 1;
    }

    LinkEditModal Input {
        width: 1fr;
    }

    LinkEditModal .buttons {
        height: 3;
        margin-top: 1;
        align: right middle;
    }

    LinkEditModal Button {
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
            yield Static(f"Edit Link: {self._link.shortLink}", classes="title")

            # URL
            with Horizontal(classes="form-row"):
                yield Label("Destination URL:", classes="form-label")
                yield Input(value=self._link.url, id="edit-url", placeholder="https://example.com")

            # Key
            with Horizontal(classes="form-row"):
                yield Label("Short Key:", classes="form-label")
                yield Input(value=self._link.key, id="edit-key", placeholder="my-link")

            # Tags
            with Horizontal(classes="form-row"):
                yield Label("Tags:", classes="form-label")
                yield Input(
                    value=", ".join(self._link.tag_names),
                    id="edit-tags",
                    placeholder="tag1, tag2",
                )

            # UTM Source
            with Horizontal(classes="form-row"):
                yield Label("UTM Source:", classes="form-label")
                yield Input(
                    value=self._link.utm_source or "",
                    id="edit-utm-source",
                    placeholder="twitter",
                )

            # UTM Medium
            with Horizontal(classes="form-row"):
                yield Label("UTM Medium:", classes="form-label")
                yield Input(
                    value=self._link.utm_medium or "",
                    id="edit-utm-medium",
                    placeholder="social",
                )

            # UTM Campaign
            with Horizontal(classes="form-row"):
                yield Label("UTM Campaign:", classes="form-label")
                yield Input(
                    value=self._link.utm_campaign or "",
                    id="edit-utm-campaign",
                    placeholder="launch",
                )

            # Buttons
            with Horizontal(classes="buttons"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Save", variant="primary", id="save-btn")

    def action_cancel(self) -> None:
        """Cancel editing."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(None)
        elif event.button.id == "save-btn":
            self._save()

    def _save(self) -> None:
        """Save the link changes."""
        url = self.query_one("#edit-url", Input).value
        key = self.query_one("#edit-key", Input).value
        tags_str = self.query_one("#edit-tags", Input).value
        utm_source = self.query_one("#edit-utm-source", Input).value
        utm_medium = self.query_one("#edit-utm-medium", Input).value
        utm_campaign = self.query_one("#edit-utm-campaign", Input).value

        # Parse tags
        tag_names = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else None

        # Build update request
        request = UpdateLinkRequest(
            url=url if url != self._link.url else None,
            key=key if key != self._link.key else None,
            tagNames=tag_names,
            utm_source=utm_source if utm_source else None,
            utm_medium=utm_medium if utm_medium else None,
            utm_campaign=utm_campaign if utm_campaign else None,
        )

        self.dismiss(request)
