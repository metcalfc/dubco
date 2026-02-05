"""Output formatting utilities using Rich."""

import csv
import json
from io import StringIO

from rich.console import Console
from rich.table import Table

from dubco_cli.models.link import Link

console = Console()
error_console = Console(stderr=True)


def format_link_table(links: list[Link], show_clicks: bool = True) -> Table:
    """Create a Rich table for displaying links."""
    table = Table(show_header=True, header_style="bold")

    table.add_column("Short Link", style="cyan")
    table.add_column("Destination URL", overflow="fold")
    table.add_column("Tags", style="yellow")
    if show_clicks:
        table.add_column("Clicks", justify="right", style="green")
    table.add_column("Created", style="dim")

    for link in links:
        tags = ", ".join(link.tag_names) if link.tag_names else "-"
        created = link.created.strftime("%Y-%m-%d")

        row = [link.shortLink, truncate(link.url, 50), tags]
        if show_clicks:
            row.append(str(link.clicks))
        row.append(created)

        table.add_row(*row)

    return table


def format_links_json(links: list[Link]) -> str:
    """Format links as JSON."""
    return json.dumps(
        [link.model_dump(exclude_none=True) for link in links],
        indent=2,
    )


def format_links_csv(links: list[Link]) -> str:
    """Format links as CSV."""
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["shortLink", "url", "key", "domain", "clicks", "tags", "createdAt"])

    # Rows
    for link in links:
        tags = ",".join(link.tag_names) if link.tag_names else ""
        writer.writerow(
            [
                link.shortLink,
                link.url,
                link.key,
                link.domain,
                link.clicks,
                tags,
                link.createdAt,
            ]
        )

    return output.getvalue()


def format_links_plain(links: list[Link]) -> str:
    """Format links as plain text, one short link per line."""
    return "\n".join(link.shortLink for link in links)


def truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def print_link_created(link: Link) -> None:
    """Print a newly created link."""
    console.print(f"[green]Created:[/green] {link.shortLink}")
    console.print(f"  [dim]Destination:[/dim] {truncate(link.url, 60)}")
    if link.tag_names:
        console.print(f"  [dim]Tags:[/dim] {', '.join(link.tag_names)}")


def print_links(links: list[Link], format: str = "table") -> None:
    """Print links in the specified format."""
    if not links:
        if format not in ("plain", "json", "csv"):
            console.print("[dim]No links found.[/dim]")
        return

    if format == "json":
        print(format_links_json(links))
    elif format == "csv":
        print(format_links_csv(links))
    elif format == "plain":
        print(format_links_plain(links))
    else:
        table = format_link_table(links)
        console.print(table)


def print_error(message: str) -> None:
    """Print an error message."""
    error_console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")
