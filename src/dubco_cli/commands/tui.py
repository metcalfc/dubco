"""TUI command for dubco-cli."""

import typer
from rich.console import Console

console = Console()


def tui() -> None:
    """Launch the interactive TUI for managing links."""
    try:
        from dubco_cli.tui.app import DubTUIApp
    except ImportError:
        console.print(
            "[red]Error:[/red] TUI dependencies not installed.\n"
            "Install with: [bold]pip install dubco-cli[tui][/bold]"
        )
        raise typer.Exit(1)

    app = DubTUIApp()
    app.run()
