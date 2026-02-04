"""List command for displaying links."""

from typing import Annotated

import typer
from rich.console import Console

from dubco_cli.api.client import DubClient, DubAPIError
from dubco_cli.api.links import list_all_links
from dubco_cli.utils.output import print_error, print_links

console = Console()


def list_links(
    domain: Annotated[
        str | None,
        typer.Option("--domain", "-d", help="Filter by domain"),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", "-t", help="Filter by tag name (can be repeated)"),
    ] = None,
    search: Annotated[
        str | None,
        typer.Option("--search", "-s", help="Search in URLs and keys"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum number of links to show"),
    ] = 50,
    format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json, csv, plain"),
    ] = "table",
    sort: Annotated[
        str,
        typer.Option("--sort", help="Sort by: createdAt, clicks, updatedAt"),
    ] = "createdAt",
):
    """List your short links.

    Examples:

        dub list

        dub list -d dub.sh -n 100

        dub list -t marketing --format json

        dub list -s "campaign" --sort clicks

        dub list -o plain | head -5
    """
    if format not in ("table", "json", "csv", "plain"):
        print_error(f"Invalid format: {format}. Use table, json, csv, or plain.")
        raise typer.Exit(2)

    if sort not in ("createdAt", "clicks", "updatedAt"):
        print_error(f"Invalid sort: {sort}. Use createdAt, clicks, or updatedAt.")
        raise typer.Exit(2)

    try:
        with DubClient() as client:
            # Only show spinner for interactive table output
            if format == "table":
                with console.status("Fetching links..."):
                    links = list_all_links(
                        client,
                        domain=domain,
                        tag_names=tag,
                        search=search,
                        sort=sort,
                        limit=limit,
                    )
            else:
                links = list_all_links(
                    client,
                    domain=domain,
                    tag_names=tag,
                    search=search,
                    sort=sort,
                    limit=limit,
                )

            print_links(links, format=format)

            if format == "table" and links:
                console.print(f"\n[dim]Showing {len(links)} links[/dim]")

    except DubAPIError as e:
        print_error(str(e))
        if e.status_code == 401:
            raise typer.Exit(3)
        raise typer.Exit(1)
