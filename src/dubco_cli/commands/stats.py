"""Stats command for viewing link analytics."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from dubco_cli.api.client import DubClient, DubAPIError
from dubco_cli.api.links import get_link
from dubco_cli.utils.output import print_error

console = Console()


def stats(
    key: Annotated[
        str,
        typer.Argument(help="Link key or ID to show stats for"),
    ],
    domain: Annotated[
        str | None,
        typer.Option("--domain", "-d", help="Domain for key lookup"),
    ] = None,
):
    """Show statistics for a link.

    Examples:

        dub stats my-link -d dub.sh

        dub stats clx1234567890
    """
    try:
        with DubClient() as client:
            # Find the link
            link = None

            with console.status("Fetching link..."):
                # Try as ID first
                if key.startswith(("clx", "link_", "ext_")):
                    link = get_link(client, link_id=key)

                # Try by key+domain
                if not link and domain:
                    link = get_link(client, domain=domain, key=key)

                # Try as external ID
                if not link:
                    link = get_link(client, external_id=key)

            if not link:
                print_error(f"Link not found: {key}")
                if not domain:
                    console.print("[dim]Tip: Try specifying --domain if looking up by key[/dim]")
                raise typer.Exit(4)

            # Display link info
            console.print(f"\n[bold]{link.shortLink}[/bold]")
            console.print(f"[dim]Destination:[/dim] {link.url}")
            console.print()

            # Stats table
            table = Table(show_header=False, box=None)
            table.add_column("Metric", style="dim")
            table.add_column("Value", style="bold")

            table.add_row("Clicks", str(link.clicks))
            table.add_row("Leads", str(link.leads))
            table.add_row("Sales", str(link.sales))
            if link.saleAmount:
                table.add_row("Revenue", f"${link.saleAmount / 100:.2f}")

            console.print(table)

            # Additional info
            console.print()
            if link.lastClicked:
                console.print(f"[dim]Last clicked:[/dim] {link.lastClicked}")
            console.print(f"[dim]Created:[/dim] {link.createdAt}")

            if link.tag_names:
                console.print(f"[dim]Tags:[/dim] {', '.join(link.tag_names)}")

            # UTM params if present
            utm_params = []
            if link.utm_source:
                utm_params.append(f"source={link.utm_source}")
            if link.utm_medium:
                utm_params.append(f"medium={link.utm_medium}")
            if link.utm_campaign:
                utm_params.append(f"campaign={link.utm_campaign}")
            if utm_params:
                console.print(f"[dim]UTM:[/dim] {', '.join(utm_params)}")

    except DubAPIError as e:
        print_error(str(e))
        if e.status_code == 401:
            raise typer.Exit(3)
        if e.status_code == 404:
            raise typer.Exit(4)
        raise typer.Exit(1)
