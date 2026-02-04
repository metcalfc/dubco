"""Main entry point for dubco-cli."""

import typer
from rich.console import Console

from dubco_cli import __version__
from dubco_cli.commands import auth

app = typer.Typer(
    name="dub",
    help="CLI for managing Dub.co short links",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"dub version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """CLI for managing Dub.co short links."""
    pass


# Register auth subcommands directly on the main app
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)
app.command(name="whoami")(auth.whoami)


# Import and register other commands (added in later phases)
def _register_commands():
    """Register all command modules."""
    try:
        from dubco_cli.commands import add
        app.command(name="add")(add.add)
    except ImportError:
        pass

    try:
        from dubco_cli.commands import list as list_cmd
        app.command(name="list")(list_cmd.list_links)
        app.command(name="ls")(list_cmd.list_links)  # Alias
    except ImportError:
        pass

    try:
        from dubco_cli.commands import rm
        app.command(name="rm")(rm.rm)
    except ImportError:
        pass

    try:
        from dubco_cli.commands import stats
        app.command(name="stats")(stats.stats)
    except ImportError:
        pass

    try:
        from dubco_cli.commands import tui
        app.command(name="tui")(tui.tui)
    except ImportError:
        pass


_register_commands()


if __name__ == "__main__":
    app()
