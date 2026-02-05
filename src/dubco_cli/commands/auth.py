"""Authentication commands for dubco-cli."""


import typer
from rich.console import Console
from rich.panel import Panel

from dubco_cli.api.oauth import OAuthFlow
from dubco_cli.config import (
    clear_credentials,
    get_client_id,
    load_credentials,
    set_client_id,
)

app = typer.Typer(help="Authentication commands")
console = Console()


def prompt_for_client_id() -> str:
    """Guide user through OAuth app setup and get client_id."""
    console.print(
        Panel(
            "[bold]Welcome to dub![/bold] Let's set up authentication.\n\n"
            "To use this CLI, you need to create an OAuth app in your Dub workspace:\n\n"
            "1. Go to: [link=https://app.dub.co/settings/oauth-apps]https://app.dub.co/settings/oauth-apps[/link]\n"
            "2. Click [bold]Create OAuth App[/bold]\n"
            "3. Fill in:\n"
            "   - Name: [cyan]dubco-cli[/cyan] (or any name you prefer)\n"
            "   - Redirect URI: [cyan]http://localhost:8484/callback[/cyan]\n"
            "4. Copy the [bold]Client ID[/bold]",
            title="OAuth App Setup",
            border_style="blue",
        )
    )
    console.print()

    client_id = typer.prompt("Paste your Client ID")
    if not client_id.strip():
        console.print("[red]Error: Client ID cannot be empty[/red]")
        raise typer.Exit(2)

    return client_id.strip()


@app.command()
def login(
    client_id: str = typer.Option(
        None,
        "--client-id",
        "-c",
        help="OAuth Client ID (will prompt if not provided)",
    ),
):
    """Log in to Dub.co via OAuth."""
    try:
        # Get or prompt for client_id
        stored_client_id = get_client_id()

        if client_id:
            # User provided new client_id
            set_client_id(client_id)
        elif stored_client_id:
            # Use existing
            client_id = stored_client_id
        else:
            # First time setup
            client_id = prompt_for_client_id()
            set_client_id(client_id)

        # Run OAuth flow
        flow = OAuthFlow(client_id)
        credentials = flow.run_login_flow()

        console.print()
        console.print(
            Panel(
                f"[green]Successfully logged in![/green]\n\n"
                f"Workspace: [bold]{credentials.workspace_name}[/bold]\n"
                f"Workspace ID: [dim]{credentials.workspace_id}[/dim]",
                title="Authentication Complete",
                border_style="green",
            )
        )

    except TimeoutError:
        console.print("[red]Error: Authentication timed out[/red]")
        raise typer.Exit(3)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(3)


@app.command()
def logout():
    """Log out and clear stored credentials."""
    credentials = load_credentials()
    if not credentials:
        console.print("Not logged in.")
        return

    clear_credentials()
    console.print("[green]Logged out successfully.[/green]")


@app.command()
def whoami():
    """Show current authentication status."""
    credentials = load_credentials()
    client_id = get_client_id()

    if not credentials:
        console.print("Not logged in. Run [bold]dub login[/bold] to authenticate.")
        raise typer.Exit(3)

    console.print(f"Workspace: [bold]{credentials.workspace_name}[/bold]")
    console.print(f"Workspace ID: [dim]{credentials.workspace_id}[/dim]")

    if client_id:
        console.print(f"Client ID: [dim]{client_id[:20]}...[/dim]")
