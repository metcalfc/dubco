"""Add command for creating links."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from dubco_cli.api.client import DubAPIError, DubClient
from dubco_cli.api.links import bulk_create_links, create_link
from dubco_cli.models.link import CreateLinkRequest
from dubco_cli.utils.csv import parse_csv, row_to_create_request
from dubco_cli.utils.output import print_error, print_link_created, print_success
from dubco_cli.utils.utm import build_utm_dict, extract_utm_from_url, merge_utm_params

console = Console()


def add(
    url: Annotated[
        str | None,
        typer.Argument(help="The destination URL to shorten"),
    ] = None,
    key: Annotated[
        str | None,
        typer.Option("--key", "-k", help="Custom short link slug"),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option("--domain", "-d", help="Short link domain"),
    ] = None,
    tag: Annotated[
        list[str] | None,
        typer.Option("--tag", "-t", help="Tag(s) to apply (can be repeated)"),
    ] = None,
    utm_source: Annotated[
        str | None,
        typer.Option("--utm-source", help="UTM source parameter"),
    ] = None,
    utm_medium: Annotated[
        str | None,
        typer.Option("--utm-medium", help="UTM medium parameter"),
    ] = None,
    utm_campaign: Annotated[
        str | None,
        typer.Option("--utm-campaign", help="UTM campaign parameter"),
    ] = None,
    utm_term: Annotated[
        str | None,
        typer.Option("--utm-term", help="UTM term parameter"),
    ] = None,
    utm_content: Annotated[
        str | None,
        typer.Option("--utm-content", help="UTM content parameter"),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="CSV file for bulk creation"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate without creating links"),
    ] = False,
):
    """Create a new short link.

    Examples:

        dub add https://example.com

        dub add https://example.com -k my-link -d dub.sh

        dub add https://example.com --utm-source twitter --utm-campaign launch

        dub add -f links.csv
    """
    if file:
        _handle_bulk_add(file, dry_run)
    elif url:
        _handle_single_add(
            url=url,
            key=key,
            domain=domain,
            tags=tag,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            dry_run=dry_run,
        )
    else:
        console.print("[red]Error: Either URL or --file is required[/red]")
        raise typer.Exit(2)


def _handle_single_add(
    url: str,
    key: str | None,
    domain: str | None,
    tags: list[str] | None,
    utm_source: str | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    utm_term: str | None,
    utm_content: str | None,
    dry_run: bool,
) -> None:
    """Handle creating a single link."""
    # Extract UTM params from URL
    clean_url, url_utm = extract_utm_from_url(url)

    # Merge CLI UTM params with URL params (CLI takes precedence)
    cli_utm = build_utm_dict(
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_term=utm_term,
        utm_content=utm_content,
    )
    final_utm = merge_utm_params(url_utm, cli_utm)

    # Build request
    request = CreateLinkRequest(
        url=clean_url,
        key=key,
        domain=domain,
        tagNames=tags if tags else None,
        **{k: v for k, v in final_utm.items() if v},
    )

    if dry_run:
        console.print("[yellow]Dry run - would create:[/yellow]")
        console.print(f"  URL: {request.url}")
        if request.key:
            console.print(f"  Key: {request.key}")
        if request.domain:
            console.print(f"  Domain: {request.domain}")
        if request.tagNames:
            console.print(f"  Tags: {', '.join(request.tagNames)}")
        for param in ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"]:
            if value := getattr(request, param):
                console.print(f"  {param}: {value}")
        return

    try:
        with DubClient() as client:
            link = create_link(client, request)
            print_link_created(link)
    except DubAPIError as e:
        print_error(str(e))
        if e.status_code == 401:
            raise typer.Exit(3)
        raise typer.Exit(1)


def _handle_bulk_add(file: Path, dry_run: bool) -> None:
    """Handle bulk creation from CSV file."""
    try:
        result = parse_csv(file)
    except FileNotFoundError:
        print_error(f"File not found: {file}")
        raise typer.Exit(2)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(2)

    # Report validation errors
    if result.invalid_rows:
        console.print("[red]Validation errors:[/red]")
        for row in result.invalid_rows:
            for error in row.errors:
                console.print(f"  Row {row.row_number}: {error}")
        console.print()

    if not result.valid_rows:
        print_error("No valid rows to process")
        raise typer.Exit(2)

    console.print(f"Found {len(result.valid_rows)} valid rows")
    if result.invalid_rows:
        console.print(f"[yellow]Skipping {len(result.invalid_rows)} invalid rows[/yellow]")

    if dry_run:
        console.print("\n[yellow]Dry run - would create:[/yellow]")
        for row in result.valid_rows[:10]:  # Show first 10
            req = row_to_create_request(row)
            console.print(f"  Row {row.row_number}: {req.url}")
            if req.key:
                console.print(f"    Key: {req.key}")
        if len(result.valid_rows) > 10:
            console.print(f"  ... and {len(result.valid_rows) - 10} more")
        return

    # Convert rows to requests
    requests = [row_to_create_request(row) for row in result.valid_rows]

    # Create links with progress
    try:
        with DubClient() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Creating {len(requests)} links...",
                    total=len(requests),
                )

                created, errors = bulk_create_links(client, requests)
                progress.update(task, completed=len(requests))

    except DubAPIError as e:
        print_error(str(e))
        if e.status_code == 401:
            raise typer.Exit(3)
        raise typer.Exit(1)

    # Report results
    console.print()
    if created:
        print_success(f"Created {len(created)} links")
        for link in created[:5]:  # Show first 5
            console.print(f"  {link.shortLink} -> {link.url[:50]}")
        if len(created) > 5:
            console.print(f"  ... and {len(created) - 5} more")

    if errors:
        console.print(f"\n[red]Failed to create {len(errors)} links:[/red]")
        for err in errors[:10]:  # Show first 10 errors
            if "row" in err:
                console.print(f"  Row {err['row']}: {err['error']}")
            else:
                console.print(f"  {err.get('url', 'Unknown')}: {err['error']}")
        if len(errors) > 10:
            console.print(f"  ... and {len(errors) - 10} more errors")
        raise typer.Exit(5)  # Partial failure
